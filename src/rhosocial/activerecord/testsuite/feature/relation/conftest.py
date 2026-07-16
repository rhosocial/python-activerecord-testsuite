# src/rhosocial/activerecord/testsuite/feature/relation/conftest.py
"""
Pytest configuration for relation tests.

This file provides the memory-based model fixtures for relation tests.
These fixtures are backend-agnostic and do not require database access.

For backend implementations that want to run these tests, they should
create their own conftest.py file and import this one:

```python
# In backend conftest.py
from rhosocial.activerecord.testsuite.feature.relation.conftest import *
```

Or copy the fixtures they need to properly configure their models.
"""
from typing import ClassVar, Any, Optional, List, Dict
import pytest
from pydantic import BaseModel

from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.cache import CacheConfig
from rhosocial.activerecord.relation.descriptors import BelongsTo, HasMany, HasOne
from rhosocial.activerecord.relation.async_descriptors import AsyncBelongsTo, AsyncHasMany, AsyncHasOne
from rhosocial.activerecord.relation.interfaces import IRelationLoader, IAsyncRelationLoader


class Employee(RelationManagementMixin, BaseModel):
    """Memory-based Employee model: used for BelongsTo -> Department testing."""
    id: int
    name: str
    department_id: int
    department: ClassVar[BelongsTo["Department"]] = BelongsTo(
        foreign_key="department_id",
        inverse_of="employees"
    )


class Department(RelationManagementMixin, BaseModel):
    """Memory-based Department model: used for HasMany -> Employee testing."""
    id: int
    name: str
    employees: ClassVar[HasMany["Employee"]] = HasMany(
        foreign_key="department_id",
        inverse_of="department"
    )


@pytest.fixture
def employee():
    """A single Employee instance (memory-based) for BelongsTo relation tests."""
    return Employee(id=1, name="John Doe", department_id=1)


@pytest.fixture
def department():
    """A single Department instance (memory-based) for HasMany relation tests."""
    return Department(id=1, name="Engineering")


@pytest.fixture
def employee_class():
    """The Employee model class (memory-based) for class-level relation queries."""
    return Employee


@pytest.fixture
def department_class():
    """The Department model class (memory-based) for class-level relation queries."""
    return Department


class CustomBookLoaderI(IRelationLoader):
    """Loader returning a synthetic Book list: used by Author.books."""

    def load(self, instance: Any) -> Optional[List[Any]]:
        return [Book(id=1, title="Test Book", author_id=instance.id)]

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAuthorLoaderI(IRelationLoader):
    """Loader returning a synthetic Author: used by Book.author."""

    def load(self, instance: Any) -> Optional[Any]:
        return Author(id=instance.author_id, name="Test Author")

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomProfileLoaderI(IRelationLoader):
    """Loader returning a synthetic Profile: used by Author.profile."""

    def load(self, instance: Any) -> Optional[Any]:
        return Profile(id=1, bio="Test Bio", author_id=instance.id)

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomChapterLoaderI(IRelationLoader):
    """Loader returning a synthetic Chapter list: used by Book.chapters."""

    def load(self, instance: Any) -> Optional[List[Any]]:
        return [Chapter(id=1, title="Test Chapter", book_id=instance.id)]

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAuthorProfileLoaderI(IRelationLoader):
    """Loader returning a synthetic Author: used by Profile.author."""

    def load(self, instance: Any) -> Optional[Any]:
        return Author(id=instance.author_id, name="Test Author")

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class Author(RelationManagementMixin, BaseModel):
    """Memory-based Author with HasMany->books and HasOne->profile, custom loader + cache TTL=1s."""

    id: int
    name: str
    books: ClassVar[HasMany["Book"]] = HasMany(
        foreign_key="author_id",
        inverse_of="author",
        loader=CustomBookLoaderI(),
        cache_config=CacheConfig(ttl=1)
    )
    profile: ClassVar[HasOne["Profile"]] = HasOne(
        foreign_key="author_id",
        inverse_of="author",
        loader=CustomProfileLoaderI()
    )


class Book(RelationManagementMixin, BaseModel):
    """Memory-based Book with BelongsTo->author and HasMany->chapters, custom loaders."""

    id: int
    title: str
    author_id: int
    author: ClassVar[BelongsTo["Author"]] = BelongsTo(
        foreign_key="author_id",
        inverse_of="books",
        loader=CustomAuthorLoaderI()
    )
    chapters: ClassVar[HasMany["Chapter"]] = HasMany(
        foreign_key="book_id",
        inverse_of="book",
        loader=CustomChapterLoaderI()  # Add the loader here
    )


class Chapter(RelationManagementMixin, BaseModel):
    """Memory-based Chapter with BelongsTo->book, no custom loader (tests default loader)."""

    id: int
    title: str
    book_id: int
    book: ClassVar[BelongsTo["Book"]] = BelongsTo(
        foreign_key="book_id",
        inverse_of="chapters"
    )


class Profile(RelationManagementMixin, BaseModel):
    """Memory-based Profile with BelongsTo->author, custom loader for the inverse side."""

    id: int
    bio: str
    author_id: int
    author: ClassVar[BelongsTo["Author"]] = BelongsTo(
        foreign_key="author_id",
        inverse_of="profile",
        loader=CustomAuthorProfileLoaderI()  # Add loader
    )


@pytest.fixture
def author():
    """An Author instance with HasMany-books and HasOne-profile, using custom loaders."""
    return Author(id=1, name="Test Author")


@pytest.fixture
def book():
    """A Book instance linked to author_id=1 with BelongsTo-author and HasMany-chapters."""
    return Book(id=1, title="Test Book", author_id=1)


@pytest.fixture
def chapter():
    """A Chapter instance linked to book_id=1 with BelongsTo-book."""
    return Chapter(id=1, title="Chapter 1", book_id=1)


@pytest.fixture
def profile():
    """A Profile instance linked to author_id=1 with BelongsTo-author + custom loader."""
    return Profile(id=1, bio="Test Bio", author_id=1)


# ── Async memory-based models (mirror of the sync Author/Book/Chapter/Profile) ──


class CustomAsyncBookLoaderI(IAsyncRelationLoader):
    """Async loader returning a synthetic Book list: used by AsyncAuthor.books."""

    async def load(self, instance: Any) -> Optional[List[Any]]:
        return [AsyncBook(id=1, title="Test Book", author_id=instance.id)]

    async def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAsyncAuthorLoaderI(IAsyncRelationLoader):
    """Async loader returning a synthetic Author: used by AsyncBook.author."""

    async def load(self, instance: Any) -> Optional[Any]:
        return AsyncAuthor(id=instance.author_id, name="Test Author")

    async def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAsyncProfileLoaderI(IAsyncRelationLoader):
    """Async loader returning a synthetic Profile: used by AsyncAuthor.profile."""

    async def load(self, instance: Any) -> Optional[Any]:
        return AsyncProfile(id=1, bio="Test Bio", author_id=instance.id)

    async def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAsyncChapterLoaderI(IAsyncRelationLoader):
    """Async loader returning a synthetic Chapter list: used by AsyncBook.chapters."""

    async def load(self, instance: Any) -> Optional[List[Any]]:
        return [AsyncChapter(id=1, title="Test Chapter", book_id=instance.id)]

    async def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAsyncAuthorProfileLoaderI(IAsyncRelationLoader):
    """Async loader returning a synthetic Author: used by AsyncProfile.author."""

    async def load(self, instance: Any) -> Optional[Any]:
        return AsyncAuthor(id=instance.author_id, name="Test Author")

    async def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class AsyncAuthor(RelationManagementMixin, BaseModel):
    """Memory-based async Author with AsyncHasMany->books and AsyncHasOne->profile, custom loader + cache TTL=1s."""

    id: int
    name: str
    books: ClassVar[AsyncHasMany["AsyncBook"]] = AsyncHasMany(
        foreign_key="author_id",
        inverse_of="author",
        loader=CustomAsyncBookLoaderI(),
        cache_config=CacheConfig(ttl=1)
    )
    profile: ClassVar[AsyncHasOne["AsyncProfile"]] = AsyncHasOne(
        foreign_key="author_id",
        inverse_of="author",
        loader=CustomAsyncProfileLoaderI()
    )


class AsyncBook(RelationManagementMixin, BaseModel):
    """Memory-based async Book with AsyncBelongsTo->author and AsyncHasMany->chapters, custom loaders."""

    id: int
    title: str
    author_id: int
    author: ClassVar[AsyncBelongsTo["AsyncAuthor"]] = AsyncBelongsTo(
        foreign_key="author_id",
        inverse_of="books",
        loader=CustomAsyncAuthorLoaderI()
    )
    chapters: ClassVar[AsyncHasMany["AsyncChapter"]] = AsyncHasMany(
        foreign_key="book_id",
        inverse_of="book",
        loader=CustomAsyncChapterLoaderI()  # Add the loader here
    )


class AsyncChapter(RelationManagementMixin, BaseModel):
    """Memory-based async Chapter with AsyncBelongsTo->book, no custom loader (tests default loader)."""

    id: int
    title: str
    book_id: int
    book: ClassVar[AsyncBelongsTo["AsyncBook"]] = AsyncBelongsTo(
        foreign_key="book_id",
        inverse_of="chapters"
    )


class AsyncProfile(RelationManagementMixin, BaseModel):
    """Memory-based async Profile with AsyncBelongsTo->author, custom loader for the inverse side."""

    id: int
    bio: str
    author_id: int
    author: ClassVar[AsyncBelongsTo["AsyncAuthor"]] = AsyncBelongsTo(
        foreign_key="author_id",
        inverse_of="profile",
        loader=CustomAsyncAuthorProfileLoaderI()  # Add loader
    )


@pytest.fixture
def async_author():
    """An AsyncAuthor instance with AsyncHasMany-books and AsyncHasOne-profile, using custom loaders."""
    return AsyncAuthor(id=1, name="Test Author")


@pytest.fixture
def async_book():
    """An AsyncBook instance linked to author_id=1 with AsyncBelongsTo-author and AsyncHasMany-chapters."""
    return AsyncBook(id=1, title="Test Book", author_id=1)


@pytest.fixture
def async_chapter():
    """An AsyncChapter instance linked to book_id=1 with AsyncBelongsTo-book."""
    return AsyncChapter(id=1, title="Chapter 1", book_id=1)


@pytest.fixture
def async_profile():
    """An AsyncProfile instance linked to author_id=1 with AsyncBelongsTo-author + custom loader."""
    return AsyncProfile(id=1, bio="Test Bio", author_id=1)


# ── Provider-based fixtures for query tests ──────────────

PROVIDER_KEY_SYNC = "feature.relation.IRelationSyncProvider"
PROVIDER_KEY_ASYNC = "feature.relation.IRelationAsyncProvider"


def get_scenarios_sync():
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


def get_scenarios_async():
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


_scenarios_sync = get_scenarios_sync()
_scenarios_async = get_scenarios_async()

SCENARIO_PARAMS_SYNC = _scenarios_sync if _scenarios_sync else [
    pytest.param("default", marks=pytest.mark.skip(reason="No sync relation testsuite scenarios found"))
]
SCENARIO_PARAMS_ASYNC = _scenarios_async if _scenarios_async else [
    pytest.param("default", marks=pytest.mark.skip(reason="No async relation testsuite scenarios found"))
]


@pytest.fixture(scope="function", autouse=True)
def check_relation_capability_requirements(request):
    """Auto-use fixture: skips tests that require unsupported backend capabilities.

    For each test, checks whether it needs a specific protocol or function support
    (via @requires_protocol / @requires_functions markers). If the model's backend
    doesn't support the required capability, the test is skipped automatically.
    """
    model_to_check = None
    fixture_options = [
        "user_class",
        "post_class",
        "comment_class",
        "user_post_comment_classes",
        "async_user_class",
        "async_post_class",
        "async_comment_class",
        "async_user_post_comment_classes",
    ]

    for fixture_name in fixture_options:
        if fixture_name not in request.fixturenames:
            continue
        try:
            fixture_value = request.getfixturevalue(fixture_name)
        except Exception:
            continue

        values = fixture_value if isinstance(fixture_value, tuple) else (fixture_value,)
        for value in values:
            if hasattr(value, "backend") or hasattr(value, "__backend__"):
                model_to_check = value
                break
        if model_to_check is not None:
            break

    if model_to_check is None:
        return

    protocol_marker = request.node.get_closest_marker("requires_protocol")
    if protocol_marker:
        from rhosocial.activerecord.testsuite.utils import skip_test_if_protocol_unsupported
        protocol_class, method_name = protocol_marker.args[0]
        skip_test_if_protocol_unsupported(model_to_check, protocol_class, method_name)

    functions_marker = request.node.get_closest_marker("requires_functions")
    if functions_marker:
        from rhosocial.activerecord.testsuite.utils import skip_test_if_functions_unsupported
        skip_test_if_functions_unsupported(model_to_check, functions_marker.args[0])


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def user_class(request):
    """Provider-backed User model class (ActiveRecord) for sync relation tests.

    Each scenario from provider.get_test_scenarios() yields a differently-configured
    User model (e.g., different database or table name). The provider cleans up
    after each test.
    """
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()
    model = provider.setup_user_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def post_class(request):
    """Provider-backed Post model class (ActiveRecord) for sync relation tests."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()
    model = provider.setup_post_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def comment_class(request):
    """Provider-backed Comment model class (ActiveRecord) for sync relation tests."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()
    model = provider.setup_comment_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def user_post_comment_classes(request):
    """Combined fixture that provides User, Post, Comment classes sharing the same backend."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()
    user = provider.setup_user_model(scenario)
    post = provider.setup_post_model(scenario)
    comment = provider.setup_comment_model(scenario)
    yield user, post, comment
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_user_class(request):
    """Provider-backed async User model class (AsyncActiveRecord) for async relation tests."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    model = await provider.setup_user_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_post_class(request):
    """Provider-backed async Post model class (AsyncActiveRecord) for async relation tests."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    model = await provider.setup_post_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_comment_class(request):
    """Provider-backed async Comment model class (AsyncActiveRecord) for async relation tests."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    model = await provider.setup_comment_model(scenario)
    yield model
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_user_post_comment_classes(request):
    """Combined fixture that provides async User, Post, Comment classes sharing the same backend."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    user = await provider.setup_user_model(scenario)
    post = await provider.setup_post_model(scenario)
    comment = await provider.setup_comment_model(scenario)
    yield user, post, comment
    await provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_SYNC)
def relation_boundary_context(request):
    """Provides relation boundary models, provider, and scenario."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_SYNC)
    provider = provider_class()
    owner, profile, post = provider.setup_relation_boundary_fixtures(scenario)
    yield provider, scenario, owner, profile, post
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS_ASYNC)
async def async_relation_boundary_context(request):
    """Provides async relation boundary models, provider, and scenario."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY_ASYNC)
    provider = provider_class()
    owner, profile, post = await provider.setup_relation_boundary_fixtures(scenario)
    yield provider, scenario, owner, profile, post
    await provider.cleanup_after_test(scenario)
