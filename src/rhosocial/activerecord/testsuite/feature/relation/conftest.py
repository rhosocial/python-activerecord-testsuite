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
from rhosocial.activerecord.relation.interfaces import IRelationLoader


class Employee(RelationManagementMixin, BaseModel):
    id: int
    name: str
    department_id: int
    department: ClassVar[BelongsTo["Department"]] = BelongsTo(
        foreign_key="department_id",
        inverse_of="employees"
    )


class Department(RelationManagementMixin, BaseModel):
    id: int
    name: str
    employees: ClassVar[HasMany["Employee"]] = HasMany(
        foreign_key="department_id",
        inverse_of="department"
    )


@pytest.fixture
def employee():
    return Employee(id=1, name="John Doe", department_id=1)


@pytest.fixture
def department():
    return Department(id=1, name="Engineering")


@pytest.fixture
def employee_class():
    return Employee


@pytest.fixture
def department_class():
    return Department


class CustomBookLoaderI(IRelationLoader):
    def load(self, instance: Any) -> Optional[List[Any]]:
        return [Book(id=1, title="Test Book", author_id=instance.id)]

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAuthorLoaderI(IRelationLoader):
    def load(self, instance: Any) -> Optional[Any]:
        return Author(id=instance.author_id, name="Test Author")

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomProfileLoaderI(IRelationLoader):
    def load(self, instance: Any) -> Optional[Any]:
        return Profile(id=1, bio="Test Bio", author_id=instance.id)

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomChapterLoaderI(IRelationLoader):
    def load(self, instance: Any) -> Optional[List[Any]]:
        return [Chapter(id=1, title="Test Chapter", book_id=instance.id)]

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class CustomAuthorProfileLoaderI(IRelationLoader):
    def load(self, instance: Any) -> Optional[Any]:
        return Author(id=instance.author_id, name="Test Author")

    def batch_load(self, instances: List[Any], base_query: Any) -> Dict[int, Any]:
        pass


class Author(RelationManagementMixin, BaseModel):
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
    id: int
    title: str
    book_id: int
    book: ClassVar[BelongsTo["Book"]] = BelongsTo(
        foreign_key="book_id",
        inverse_of="chapters"
    )


class Profile(RelationManagementMixin, BaseModel):
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
    return Author(id=1, name="Test Author")


@pytest.fixture
def book():
    return Book(id=1, title="Test Book", author_id=1)


@pytest.fixture
def chapter():
    return Chapter(id=1, title="Chapter 1", book_id=1)


@pytest.fixture
def profile():
    return Profile(id=1, bio="Test Bio", author_id=1)


# ── Provider-based fixtures for query tests ──────────────

PROVIDER_KEY = "feature.relation.IRelationProvider"


def get_scenarios():
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    if not provider_class:
        return []
    return provider_class().get_test_scenarios()


_scenarios = get_scenarios()
SCENARIO_PARAMS = _scenarios if _scenarios else [
    pytest.param("default", marks=pytest.mark.skip(reason="No relation testsuite scenarios found"))
]


@pytest.fixture(scope="function", autouse=True)
def check_relation_capability_requirements(request):
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


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def user_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_user_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def post_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_post_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def comment_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_comment_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def user_post_comment_classes(request):
    """Combined fixture that provides User, Post, Comment classes sharing the same backend."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    user = provider.setup_user_model(scenario)
    post = provider.setup_post_model(scenario)
    comment = provider.setup_comment_model(scenario)
    yield user, post, comment
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def async_user_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_async_user_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def async_post_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_async_post_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def async_comment_class(request):
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    model = provider.setup_async_comment_model(scenario)
    yield model
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def async_user_post_comment_classes(request):
    """Combined fixture that provides async User, Post, Comment classes sharing the same backend."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    user = provider.setup_async_user_model(scenario)
    post = provider.setup_async_post_model(scenario)
    comment = provider.setup_async_comment_model(scenario)
    yield user, post, comment
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def relation_boundary_context(request):
    """Provides relation boundary models, provider, and scenario."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    owner, profile, post = provider.setup_relation_boundary_fixtures(scenario)
    yield provider, scenario, owner, profile, post
    provider.cleanup_after_test(scenario)


@pytest.fixture(scope="function", params=SCENARIO_PARAMS)
def async_relation_boundary_context(request):
    """Provides async relation boundary models, provider, and scenario."""
    from rhosocial.activerecord.testsuite.core.registry import get_provider_registry
    scenario = request.param
    provider_registry = get_provider_registry()
    provider_class = provider_registry.get_provider(PROVIDER_KEY)
    provider = provider_class()
    owner, profile, post = provider.setup_async_relation_boundary_fixtures(scenario)
    yield provider, scenario, owner, profile, post
    provider.cleanup_after_test(scenario)
