# src/rhosocial/activerecord/testsuite/feature/relation/conftest.py
"""L2 environment and model fixtures shared by the relation topic.

- the memory models below stand in for records that never touch a database;
- ``database``/``database_config``/``schema`` serve the directories that have
  no conftest of their own (``relation/core`` in the backends); every subdirectory
  that owns a database overrides them in its own conftest;
- the database-backed model fixtures configure their model against the
  directory's database.  Which versioned model file supplies a class is decided
  here, so tests only see fixture names.
"""

from pathlib import Path
from typing import ClassVar, Any, Optional, List, Dict
import pytest
from pydantic import BaseModel

from rhosocial.activerecord.backend.options import ExecutionOptions
from rhosocial.activerecord.backend.schema import StatementType
from rhosocial.activerecord.relation.base import RelationManagementMixin
from rhosocial.activerecord.relation.cache import CacheConfig
from rhosocial.activerecord.relation.descriptors import BelongsTo, HasMany, HasOne
from rhosocial.activerecord.relation.async_descriptors import (
    AsyncBelongsTo,
    AsyncHasMany,
    AsyncHasOne,
)
from rhosocial.activerecord.relation.interfaces import IRelationLoader, IAsyncRelationLoader

from .fixtures import resolve
from .fixtures.definitions import (
    CommentDefinition,
    PostDefinition,
    UserDefinition,
)


class Employee(RelationManagementMixin, BaseModel):
    """Memory-based Employee model: used for BelongsTo -> Department testing."""

    id: int
    name: str
    department_id: int
    department: ClassVar[BelongsTo["Department"]] = BelongsTo(
        foreign_key="department_id", inverse_of="employees"
    )


class Department(RelationManagementMixin, BaseModel):
    """Memory-based Department model: used for HasMany -> Employee testing."""

    id: int
    name: str
    employees: ClassVar[HasMany["Employee"]] = HasMany(
        foreign_key="department_id", inverse_of="department"
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
        cache_config=CacheConfig(ttl=1),
    )
    profile: ClassVar[HasOne["Profile"]] = HasOne(
        foreign_key="author_id", inverse_of="author", loader=CustomProfileLoaderI()
    )


class Book(RelationManagementMixin, BaseModel):
    """Memory-based Book with BelongsTo->author and HasMany->chapters, custom loaders."""

    id: int
    title: str
    author_id: int
    author: ClassVar[BelongsTo["Author"]] = BelongsTo(
        foreign_key="author_id", inverse_of="books", loader=CustomAuthorLoaderI()
    )
    chapters: ClassVar[HasMany["Chapter"]] = HasMany(
        foreign_key="book_id",
        inverse_of="book",
        loader=CustomChapterLoaderI(),  # Add the loader here
    )


class Chapter(RelationManagementMixin, BaseModel):
    """Memory-based Chapter with BelongsTo->book, no custom loader (tests default loader)."""

    id: int
    title: str
    book_id: int
    book: ClassVar[BelongsTo["Book"]] = BelongsTo(foreign_key="book_id", inverse_of="chapters")


class Profile(RelationManagementMixin, BaseModel):
    """Memory-based Profile with BelongsTo->author, custom loader for the inverse side."""

    id: int
    bio: str
    author_id: int
    author: ClassVar[BelongsTo["Author"]] = BelongsTo(
        foreign_key="author_id",
        inverse_of="profile",
        loader=CustomAuthorProfileLoaderI(),  # Add loader
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
        cache_config=CacheConfig(ttl=1),
    )
    profile: ClassVar[AsyncHasOne["AsyncProfile"]] = AsyncHasOne(
        foreign_key="author_id", inverse_of="author", loader=CustomAsyncProfileLoaderI()
    )


class AsyncBook(RelationManagementMixin, BaseModel):
    """Memory-based async Book with AsyncBelongsTo->author and AsyncHasMany->chapters, custom loaders."""

    id: int
    title: str
    author_id: int
    author: ClassVar[AsyncBelongsTo["AsyncAuthor"]] = AsyncBelongsTo(
        foreign_key="author_id", inverse_of="books", loader=CustomAsyncAuthorLoaderI()
    )
    chapters: ClassVar[AsyncHasMany["AsyncChapter"]] = AsyncHasMany(
        foreign_key="book_id",
        inverse_of="book",
        loader=CustomAsyncChapterLoaderI(),  # Add the loader here
    )


class AsyncChapter(RelationManagementMixin, BaseModel):
    """Memory-based async Chapter with AsyncBelongsTo->book, no custom loader (tests default loader)."""

    id: int
    title: str
    book_id: int
    book: ClassVar[AsyncBelongsTo["AsyncBook"]] = AsyncBelongsTo(
        foreign_key="book_id", inverse_of="chapters"
    )


class AsyncProfile(RelationManagementMixin, BaseModel):
    """Memory-based async Profile with AsyncBelongsTo->author, custom loader for the inverse side."""

    id: int
    bio: str
    author_id: int
    author: ClassVar[AsyncBelongsTo["AsyncAuthor"]] = AsyncBelongsTo(
        foreign_key="author_id",
        inverse_of="profile",
        loader=CustomAsyncAuthorProfileLoaderI(),  # Add loader
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


# ── Database-backed fixtures ─────────────────────────────
#
# The class a fixture delivers is selected here, not by the test; the fixture
# only configures it against the directory's database and disconnects after.

DbEmployee = resolve("Employee")
DbDepartment = resolve("Department")
DbAuthor = resolve("Author")
DbBook = resolve("Book")
DbChapter = resolve("Chapter")
DbProfile = resolve("Profile")
User = resolve("User")
AsyncUser = resolve("AsyncUser")
Post = resolve("Post")
AsyncPost = resolve("AsyncPost")
Comment = resolve("Comment")
AsyncComment = resolve("AsyncComment")
BoundaryOwner = resolve("BoundaryOwner")
BoundaryProfile = resolve("BoundaryProfile")
BoundaryPost = resolve("BoundaryPost")
AsyncBoundaryOwner = resolve("AsyncBoundaryOwner")
AsyncBoundaryProfile = resolve("AsyncBoundaryProfile")
AsyncBoundaryPost = resolve("AsyncBoundaryPost")

DDL = ExecutionOptions(stmt_type=StatementType.DDL)

DEFINITIONS = (UserDefinition, PostDefinition, CommentDefinition)


def _database_name() -> str:
    """Database name from this conftest's namespace (below ``feature``)."""
    parts = Path(__file__).parent.parts
    start = parts.index("feature") + 1
    return "test_" + "_".join(parts[start:])


@pytest.fixture(scope="session")
def database_config(backend_scenario):
    """The scenario, its connection configuration, and the directory database name."""
    name = _database_name()
    return backend_scenario, backend_scenario.make_config(name), name


@pytest.fixture(scope="session")
def database(database_config):
    """The topic's database, prepared once for the directories without an L2."""
    scenario, config, name = database_config
    scenario.reset_database(name)
    backend = scenario.backend_class(connection_config=config)
    backend.connect()
    backend.introspect_and_adapt()
    yield backend
    backend.disconnect()


@pytest.fixture(scope="function")
def schema(database):
    """Drop and recreate the topic tables for every test that asks for them.

    Subdirectories that own a database override this fixture with their own
    autouse ``schema``; the memory-only directories never request it.
    """
    fixtures = [definition(database.dialect) for definition in DEFINITIONS]
    for fixture in fixtures:
        database.execute(*fixture.create_table.to_sql(), options=DDL)
    yield
    for fixture in reversed(fixtures):
        database.execute(*fixture.drop_table.to_sql(), options=DDL)


class BoundaryDataset:
    """The rows the relation boundary tests read."""

    def __init__(self, owner, profile, post):
        self.owner = owner
        self.profile = profile
        self.post = post

    def load_relation_boundary_dataset(self, scenario, name):
        if name == "owner_without_children":
            record = self.owner(name="owner")
            record.save()
            return {"owner_id": record.id}
        if name == "null_foreign_key":
            record = self.owner(name="owner")
            record.save()
            profile = self.profile(bio="bio", owner_id=None)
            profile.save()
            post = self.post(title="post", owner_id=record.id)
            post.save()
            return {"owner_id": record.id, "profile_id": profile.id, "post_id": post.id}
        if name == "orphan_foreign_key":
            record = self.owner(name="owner")
            record.save()
            profile = self.profile(bio="bio", owner_id=987654)
            profile.save()
            post = self.post(title="post", owner_id=987654)
            post.save()
            return {
                "owner_id": record.id,
                "profile_id": profile.id,
                "post_id": post.id,
                "missing_owner_id": 987654,
            }
        if name == "multiple_has_one_matches":
            record = self.owner(name="owner")
            record.save()
            first = self.profile(bio="first", owner_id=record.id)
            first.save()
            second = self.profile(bio="second", owner_id=record.id)
            second.save()
            return {
                "owner_id": record.id,
                "first_profile_id": first.id,
                "second_profile_id": second.id,
            }
        raise KeyError(f"unknown boundary dataset {name!r}")


class AsyncBoundaryDataset:
    """Async counterpart of :class:`BoundaryDataset`."""

    def __init__(self, owner, profile, post):
        self.owner = owner
        self.profile = profile
        self.post = post

    async def load_relation_boundary_dataset(self, scenario, name):
        if name == "owner_without_children":
            record = self.owner(name="owner")
            await record.save()
            return {"owner_id": record.id}
        if name == "null_foreign_key":
            record = self.owner(name="owner")
            await record.save()
            profile = self.profile(bio="bio", owner_id=None)
            await profile.save()
            post = self.post(title="post", owner_id=record.id)
            await post.save()
            return {"owner_id": record.id, "profile_id": profile.id, "post_id": post.id}
        if name == "orphan_foreign_key":
            record = self.owner(name="owner")
            await record.save()
            profile = self.profile(bio="bio", owner_id=987654)
            await profile.save()
            post = self.post(title="post", owner_id=987654)
            await post.save()
            return {
                "owner_id": record.id,
                "profile_id": profile.id,
                "post_id": post.id,
                "missing_owner_id": 987654,
            }
        if name == "multiple_has_one_matches":
            record = self.owner(name="owner")
            await record.save()
            first = self.profile(bio="first", owner_id=record.id)
            await first.save()
            second = self.profile(bio="second", owner_id=record.id)
            await second.save()
            return {
                "owner_id": record.id,
                "first_profile_id": first.id,
                "second_profile_id": second.id,
            }
        raise KeyError(f"unknown boundary dataset {name!r}")


@pytest.fixture(name="user_class")
def user_class(database_config, schema):
    scenario, config, _name = database_config
    User.configure(config, scenario.backend_class)
    yield User
    User.backend().disconnect()


@pytest.fixture(name="async_user_class")
async def async_user_class(database_config, schema):
    scenario, config, _name = database_config
    await AsyncUser.configure(config, scenario.async_backend_class)
    yield AsyncUser
    await AsyncUser.backend().disconnect()


@pytest.fixture(name="post_class")
def post_class(database_config, schema):
    scenario, config, _name = database_config
    Post.configure(config, scenario.backend_class)
    yield Post
    Post.backend().disconnect()


@pytest.fixture(name="async_post_class")
async def async_post_class(database_config, schema):
    scenario, config, _name = database_config
    await AsyncPost.configure(config, scenario.async_backend_class)
    yield AsyncPost
    await AsyncPost.backend().disconnect()


@pytest.fixture(name="comment_class")
def comment_class(database_config, schema):
    scenario, config, _name = database_config
    Comment.configure(config, scenario.backend_class)
    yield Comment
    Comment.backend().disconnect()


@pytest.fixture(name="async_comment_class")
async def async_comment_class(database_config, schema):
    scenario, config, _name = database_config
    await AsyncComment.configure(config, scenario.async_backend_class)
    yield AsyncComment
    await AsyncComment.backend().disconnect()


@pytest.fixture(name="user_post_comment_classes")
def user_post_comment_classes(database_config, schema):
    scenario, config, _name = database_config
    models = (User, Post, Comment)
    for model in models:
        model.configure(config, scenario.backend_class)
    yield models
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="async_user_post_comment_classes")
async def async_user_post_comment_classes(database_config, schema):
    scenario, config, _name = database_config
    models = (AsyncUser, AsyncPost, AsyncComment)
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    yield models
    for model in models:
        await model.backend().disconnect()


@pytest.fixture(name="employee_department_fixtures")
def employee_department_fixtures(database_config):
    scenario, config, _name = database_config
    models = (DbEmployee, DbDepartment)
    for model in models:
        model.configure(config, scenario.backend_class)
    yield models
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="author_book_fixtures")
def author_book_fixtures(database_config):
    scenario, config, _name = database_config
    models = (DbAuthor, DbBook, DbChapter, DbProfile)
    for model in models:
        model.configure(config, scenario.backend_class)
    yield models
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="relation_boundary_context")
def relation_boundary_context(database_config, schema):
    scenario, config, _name = database_config
    owner = BoundaryOwner
    profile = BoundaryProfile
    post = BoundaryPost
    models = (owner, profile, post)
    for model in models:
        model.configure(config, scenario.backend_class)
    dataset = BoundaryDataset(owner, profile, post)
    yield dataset, scenario, owner, profile, post
    for model in models:
        model.backend().disconnect()


@pytest.fixture(name="async_relation_boundary_context")
async def async_relation_boundary_context(database_config, schema):
    scenario, config, _name = database_config
    owner = AsyncBoundaryOwner
    profile = AsyncBoundaryProfile
    post = AsyncBoundaryPost
    models = (owner, profile, post)
    for model in models:
        await model.configure(config, scenario.async_backend_class)
    dataset = AsyncBoundaryDataset(owner, profile, post)
    yield dataset, scenario, owner, profile, post
    for model in models:
        await model.backend().disconnect()
