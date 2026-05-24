# src/rhosocial/activerecord/testsuite/feature/query/test_logging_data_summarization.py
import copy
import json
from pathlib import Path
from typing import Iterable

import pytest

from rhosocial.activerecord.logging import LoggingConfig, LogDataMode, SummarizerConfig


SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLE_SOURCES = {
    "python_home.html": "https://www.python.org/",
    "plant_catalog.xml": "https://www.w3schools.com/xml/plant_catalog.xml",
    "jsonplaceholder_posts.json": "https://jsonplaceholder.typicode.com/posts",
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


def _create_user(User):
    user = User(username="web-content-user", email="web-content@example.com", age=30)
    user.save()
    return user


def _create_posts(Post, user_id: int, samples):
    posts = []
    for title, key in (
        ("HTML sample", "html_content"),
        ("XML sample", "xml_content"),
        ("JSON sample", "json_content"),
    ):
        post = Post(user_id=user_id, title=title, content=samples[key], status="published")
        post.save()
        posts.append(post)
    return posts


def _find_post(Post, title: str):
    results = Post.query().where(Post.c.title == title).all()
    assert len(results) == 1
    return results[0]


def _assert_round_trip_and_summary(Post, samples):
    config = _make_logging_config()
    payload = {}

    for title, key in (
        ("HTML sample", "html_content"),
        ("XML sample", "xml_content"),
        ("JSON sample", "json_content"),
    ):
        found = _find_post(Post, title)
        original = samples[key]
        assert found.content == original
        assert len(found.content) == len(original)
        payload[key] = found.content

    before = copy.deepcopy(payload)
    summary = config.summarize_data(payload)

    for key, original in payload.items():
        _assert_truncated(summary[key], original)

    assert payload == before
    assert _find_post(Post, "HTML sample").content == samples["html_content"]
    assert json.loads(_find_post(Post, "JSON sample").content)[0]["userId"] == 1


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


class TestLoggingDataSummarization:
    def test_long_web_content_is_truncated_in_summary_not_storage(self, blog_fixtures):
        User, Post, _ = blog_fixtures
        samples = _sample_contents()
        _assert_sample_integrity(samples)

        user = _create_user(User)
        _create_posts(Post, user.id, samples)

        _assert_round_trip_and_summary(Post, samples)

    def test_sensitive_fields_are_masked_in_query_payload(self, blog_fixtures):
        User, Post, _ = blog_fixtures
        samples = _sample_contents()
        user = _create_user(User)
        posts = _create_posts(Post, user.id, samples)

        _assert_sensitive_payload_summary(posts[0], samples)
        assert _find_post(Post, "HTML sample").content == samples["html_content"]

    def test_json_fixture_preserves_sample_json_round_trip(self, json_user_fixture):
        JsonUser = json_user_fixture
        json_content = _read_sample("jsonplaceholder_posts.json")
        user = JsonUser(
            username="json-content-user",
            email="json-content@example.com",
            age=28,
            preferences=json_content,
        )
        user.save()

        results = JsonUser.query().where(JsonUser.c.username == "json-content-user").all()
        assert len(results) == 1
        found = results[0]
        assert found.preferences == json_content
        assert json.loads(found.preferences)[0]["userId"] == 1

        summary = _make_logging_config().summarize_data({"preferences": found.preferences})
        _assert_truncated(summary["preferences"], json_content)
        assert found.preferences == json_content


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
    @pytest.mark.asyncio
    async def test_long_web_content_is_truncated_in_summary_not_storage(self, async_blog_fixtures):
        User, Post, _ = async_blog_fixtures
        samples = _sample_contents()
        _assert_sample_integrity(samples)

        user = await _async_create_user(User)
        await _async_create_posts(Post, user.id, samples)

        await _async_assert_round_trip_and_summary(Post, samples)

    @pytest.mark.asyncio
    async def test_sensitive_fields_are_masked_in_query_payload(self, async_blog_fixtures):
        User, Post, _ = async_blog_fixtures
        samples = _sample_contents()
        user = await _async_create_user(User)
        posts = await _async_create_posts(Post, user.id, samples)

        _assert_sensitive_payload_summary(posts[0], samples)
        found_html = await _async_find_post(Post, "HTML sample")
        assert found_html.content == samples["html_content"]
