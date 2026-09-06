# src/rhosocial/activerecord/testsuite/feature/query/logging/test_logging_data_summarization_async.py
"""Async tests for logging data summarization and masking in query log payloads."""
import copy
import json
from pathlib import Path
from typing import Iterable


from rhosocial.activerecord.logging import LoggingConfig, LogDataMode, SummarizerConfig


def _normalize_json_value(value):
    """Normalize a JSON field value for cross-backend comparison.

    Backends with native JSON types (MySQL JSON, PostgreSQL JSONB) may
    return Python dict/list instead of str. Convert everything to a
    consistent string representation for comparison and summarization.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


SAMPLES_DIR = Path(__file__).parent.parent / "samples"
SAMPLE_SOURCES = {
    "python_home.html": "https://www.python.org/",
    "plant_catalog.xml": "https://www.w3schools.com/xml/plant_catalog.xml",
    "jsonplaceholder_posts.json": "https://jsonplaceholder.typicode.com/posts",
    "unicode_multilingual.html": "https://example.com/unicode_multilingual.html",
    "unicode_multilingual.xml": "https://example.com/unicode_multilingual.xml",
    "unicode_multilingual.json": "https://example.com/unicode_multilingual.json",
}
MASKED = "***MASKED***"
MAX_STRING_LENGTH = 80


def _read_sample(name: str) -> str:
    return (SAMPLES_DIR / name).read_text(encoding="utf-8")


def _sample_contents():
    return {
        "html_content": _read_sample("python_home.html"),
        "xml_content": _read_sample("plant_catalog.xml"),
        "json_content": _read_sample("jsonplaceholder_posts.json"),
    }


def _unicode_sample_contents():
    return {
        "unicode_html": _read_sample("unicode_multilingual.html"),
        "unicode_xml": _read_sample("unicode_multilingual.xml"),
        "unicode_json": _read_sample("unicode_multilingual.json"),
    }


def _make_logging_config() -> LoggingConfig:
    return LoggingConfig(
        log_data_mode=LogDataMode.SUMMARY,
        summarizer_config=SummarizerConfig(max_string_length=MAX_STRING_LENGTH),
    )


def _assert_truncated(summary_value: str, original: str) -> None:
    assert summary_value != original
    assert summary_value.startswith(original[:MAX_STRING_LENGTH])
    assert "truncated" in summary_value
    assert f"{len(original)} chars total" in summary_value


def _assert_secrets_not_leaked(summary: object, secrets: Iterable[str]) -> None:
    rendered = str(summary)
    for secret in secrets:
        assert secret not in rendered


def _assert_sample_integrity(samples):
    html_content = samples["html_content"]
    xml_content = samples["xml_content"]
    json_content = samples["json_content"]

    assert "<html" in html_content.lower() or "<!doctype html" in html_content.lower()
    assert "<CATALOG>" in xml_content or "<catalog>" in xml_content.lower()
    parsed_json = json.loads(json_content)
    assert isinstance(parsed_json, list)
    assert parsed_json


def _assert_sensitive_payload_summary(post, samples):
    config = _make_logging_config()
    secrets = [
        "sample-password-from-test",
        "sample-token-from-test",
        "sample-api-key-from-test",
        "sample-refresh-token-from-test",
    ]
    payload = {
        "post_id": post.id,
        "title": post.title,
        "content": post.content,
        "password": secrets[0],
        "token": secrets[1],
        "api_key": secrets[2],
        "nested": {
            "refresh_token": secrets[3],
            "html": samples["html_content"],
        },
    }
    before = copy.deepcopy(payload)

    summary = config.summarize_data(payload)

    assert summary["password"] == MASKED
    assert summary["token"] == MASKED
    assert summary["api_key"] == MASKED
    assert summary["nested"]["refresh_token"] == MASKED
    assert summary["title"] == post.title
    _assert_truncated(summary["content"], post.content)
    _assert_truncated(summary["nested"]["html"], samples["html_content"])
    _assert_secrets_not_leaked(summary, secrets)
    assert payload == before


def _assert_unicode_integrity(samples):
    unicode_html = samples["unicode_html"]
    unicode_xml = samples["unicode_xml"]
    unicode_json = samples["unicode_json"]

    # Verify multi-script content is preserved
    assert "中文" in unicode_html or "日本語" in unicode_html
    assert "العربية" in unicode_html or "עברית" in unicode_html
    assert "हिन्दी" in unicode_html or "ภาษาไทย" in unicode_html

    # Verify emoji content is preserved
    assert "😀" in unicode_html
    assert "👍" in unicode_html
    assert "👨‍👩‍👧‍👦" in unicode_html

    # Verify XML structure
    assert "<UNICODE_CATALOG" in unicode_xml
    assert "你好" in unicode_xml
    assert "😀" in unicode_xml

    # Verify JSON structure
    parsed = json.loads(unicode_json)
    assert isinstance(parsed, list)
    assert len(parsed) >= 7
    greetings = parsed[0].get("greetings", {})
    assert "zh" in greetings and "ar" in greetings and "he" in greetings
    assert "😀" in str(parsed)


async def _async_create_user(User):
    user = User(username="async-web-content-user", email="async-web-content@example.com", age=30)
    await user.save()
    return user


async def _async_create_posts(Post, user_id: int, samples):
    posts = []
    for title, key in (
        ("HTML sample", "html_content"),
        ("XML sample", "xml_content"),
        ("JSON sample", "json_content"),
    ):
        post = Post(user_id=user_id, title=title, content=samples[key], status="published")
        await post.save()
        posts.append(post)
    return posts


async def _async_find_post(Post, title: str):
    results = await Post.query().where(Post.c.title == title).all()
    assert len(results) == 1
    return results[0]


async def _async_create_unicode_posts(Post, user_id: int, samples):
    posts = []
    for title, key in (
        ("Unicode HTML sample", "unicode_html"),
        ("Unicode XML sample", "unicode_xml"),
        ("Unicode JSON sample", "unicode_json"),
    ):
        post = Post(user_id=user_id, title=title, content=samples[key], status="published")
        await post.save()
        posts.append(post)
    return posts


async def _async_assert_unicode_round_trip(Post, samples):
    config = _make_logging_config()
    payload = {}

    for title, key in (
        ("Unicode HTML sample", "unicode_html"),
        ("Unicode XML sample", "unicode_xml"),
        ("Unicode JSON sample", "unicode_json"),
    ):
        found = await _async_find_post(Post, title)
        original = samples[key]
        assert found.content == original
        assert len(found.content) == len(original)
        payload[key] = found.content

    before = copy.deepcopy(payload)
    summary = config.summarize_data(payload)

    for key, original in payload.items():
        _assert_truncated(summary[key], original)

    assert payload == before


async def _async_create_injection_payload_post(Post, user_id: int):
    payloads = [
        "'; DROP TABLE users--",
        "admin' OR '1'='1",
        "' UNION SELECT * FROM information_schema.tables--",
        "x'; WAITFOR DELAY '0:0:5'--",
        "'; EXEC xp_cmdshell 'dir'--",
        "1' AND SLEEP(5)--",
        "1' AND BENCHMARK(10000000,MD5(1))--",
    ]
    content = "\n---PAYLOAD-SEPARATOR---\n".join(payloads)
    post = Post(user_id=user_id, title="SQL injection payloads", content=content, status="published")
    await post.save()
    return content, post


async def _async_assert_multilingual_text_round_trip(Post):
    texts = {
        "Chinese": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
        "Arabic": "هذا النص باللغة العربية يحتوي على اختبار شامل للترجمة",
        "Hebrew": "זוהי דוגמה לטקסט בעברית שנכתב מימין לשמאל",
        "Hindi": "यह हिन्दी भाषा में लिखा गया पाठ है। देवनागरी लिपि में",
        "Thai": "นี่คือข้อความภาษาไทย ภาษาไทยมีพยัญชนะ สระ วรรณยุกต์",
        "Russian": "Съешь ещё этих мягких французских булок да выпей чаю",
        "Korean": "한글은 세종대왕이 창제한 과학적인 문자입니다",
        "Japanese": "いろはにほへと ちりぬるを わかよたれそ つねならむ",
    }
    for lang, text in texts.items():
        post = Post(user_id=1, title=f"Multilingual-{lang}", content=text, status="published")
        await post.save()

        found = await _async_find_post(Post, f"Multilingual-{lang}")
        assert found.content == text
        assert len(found.content) == len(text)


async def _async_assert_emoji_round_trip(Post):
    long_emoji = "😀" * 200
    post = Post(user_id=1, title="Emoji burst", content=long_emoji, status="published")
    await post.save()
    results = await Post.query().where(Post.c.title == "Emoji burst").all()
    assert len(results) == 1
    found = results[0]
    assert found.content == long_emoji
    assert len(found.content) == len(long_emoji)

    config = _make_logging_config()
    summary = config.summarize_data({"content": found.content})
    _assert_truncated(summary["content"], long_emoji)
    assert found.content == long_emoji


async def _async_assert_round_trip_and_summary(Post, samples):
    config = _make_logging_config()
    payload = {}

    for title, key in (
        ("HTML sample", "html_content"),
        ("XML sample", "xml_content"),
        ("JSON sample", "json_content"),
    ):
        found = await _async_find_post(Post, title)
        original = samples[key]
        assert found.content == original
        assert len(found.content) == len(original)
        payload[key] = found.content

    before = copy.deepcopy(payload)
    summary = config.summarize_data(payload)

    for key, original in payload.items():
        _assert_truncated(summary[key], original)

    assert payload == before
    found_json = await _async_find_post(Post, "JSON sample")
    assert json.loads(found_json.content)[0]["userId"] == 1


class TestAsyncLoggingDataSummarization:
    """Async: verify query logging summarizes and masks sensitive data without altering storage."""

    async def test_long_web_content_is_truncated_in_summary_not_storage(self, async_blog_fixtures):
        """Long web content should be truncated in the summary but preserved in storage."""
        User, Post, _ = async_blog_fixtures
        samples = _sample_contents()
        _assert_sample_integrity(samples)

        user = await _async_create_user(User)
        await _async_create_posts(Post, user.id, samples)

        await _async_assert_round_trip_and_summary(Post, samples)

    async def test_sensitive_fields_are_masked_in_query_payload(self, async_blog_fixtures):
        """Sensitive fields should be masked in the query log payload."""
        User, Post, _ = async_blog_fixtures
        samples = _sample_contents()
        user = await _async_create_user(User)
        posts = await _async_create_posts(Post, user.id, samples)

        _assert_sensitive_payload_summary(posts[0], samples)
        found_html = await _async_find_post(Post, "HTML sample")
        assert found_html.content == samples["html_content"], \
            "stored content should remain unchanged after masking"

    async def test_json_fixture_preserves_sample_json_round_trip(self, async_json_user_fixture):
        """JSON fixture should preserve the sample JSON through a save/load round trip."""
        JsonUser = async_json_user_fixture
        json_content = _read_sample("jsonplaceholder_posts.json")
        original_data = json.loads(json_content)
        user = JsonUser(
            username="async-json-content-user",
            email="async-json-content@example.com",
            age=28,
            preferences=json_content,
        )
        await user.save()

        results = await JsonUser.query().where(JsonUser.c.username == "async-json-content-user").all()
        assert len(results) == 1, "query should return exactly one JSON user"
        found = results[0]

        retrieved_data = json.loads(_normalize_json_value(found.preferences))
        assert retrieved_data == original_data, "retrieved JSON should match the original data"
        assert retrieved_data[0]["userId"] == 1, "first post userId should be 1"

        prefs_str = _normalize_json_value(found.preferences)
        summary = _make_logging_config().summarize_data({"preferences": prefs_str})
        _assert_truncated(summary["preferences"], prefs_str)

    async def test_unicode_multilingual_content_round_trip(self, async_blog_fixtures):
        """Unicode multilingual content should survive a save/load round trip."""
        User, Post, _ = async_blog_fixtures
        samples = _unicode_sample_contents()
        _assert_unicode_integrity(samples)

        user = await _async_create_user(User)
        await _async_create_unicode_posts(Post, user.id, samples)

        await _async_assert_unicode_round_trip(Post, samples)

    async def test_unicode_emoji_burst_truncated_in_summary(self, async_blog_fixtures):
        """Long emoji bursts should be truncated in the summary but not in storage."""
        User, Post, _ = async_blog_fixtures
        user = await _async_create_user(User)
        await _async_assert_emoji_round_trip(Post)

    async def test_sql_injection_payloads_as_content_round_trip(self, async_blog_fixtures):
        """SQL injection payload text should be preserved verbatim as content."""
        User, Post, _ = async_blog_fixtures
        user = await _async_create_user(User)
        content, _ = await _async_create_injection_payload_post(Post, user.id)
        found = await _async_find_post(Post, "SQL injection payloads")
        assert found.content == content, "stored content should match the injected payload"
        assert len(found.content) == len(content), "stored content length should be preserved"

    async def test_multilingual_text_preserved_round_trip(self, async_blog_fixtures):
        """Multilingual text in many scripts should be preserved verbatim."""
        User, Post, _ = async_blog_fixtures
        user = await _async_create_user(User)
        await _async_assert_multilingual_text_round_trip(Post)

    async def test_unicode_json_fixture_json_field_round_trip(self, async_json_user_fixture):
        """Unicode JSON fixture should preserve its JSON field through a round trip."""
        JsonUser = async_json_user_fixture
        json_content = _read_sample("unicode_multilingual.json")
        original_data = json.loads(json_content)
        user = JsonUser(
            username="async-unicode-json-user",
            email="async-unicode-json@example.com",
            age=28,
            preferences=json_content,
        )
        await user.save()

        results = await JsonUser.query().where(JsonUser.c.username == "async-unicode-json-user").all()
        assert len(results) == 1, "query should return exactly one unicode JSON user"
        found = results[0]

        retrieved = json.loads(_normalize_json_value(found.preferences))
        assert retrieved == original_data, "retrieved JSON should match the original data"
        assert retrieved[0]["greetings"]["zh"] == "你好，世界！", "Chinese greeting should be preserved"
        assert retrieved[0]["greetings"]["ar"] == "مرحباً بالعالم!", "Arabic greeting should be preserved"

        prefs_str = _normalize_json_value(found.preferences)
        summary = _make_logging_config().summarize_data({"preferences": prefs_str})
        _assert_truncated(summary["preferences"], prefs_str)