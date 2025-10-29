# src/rhosocial/activerecord/testsuite/feature/relation/fixtures/models.py
"""
Relation model fixtures for the testsuite.
"""
from rhosocial.activerecord import ActiveRecord
from rhosocial.activerecord.relation.descriptors import BelongsTo, HasMany, HasOne


class Employee(ActiveRecord):
    username: str
    department_id: int

    # Define the relation to department
    department: BelongsTo["Department"] = BelongsTo(
        foreign_key="department_id",
        inverse_of="employees"
    )


class Department(ActiveRecord):
    name: str
    description: str = ""

    # Define the relation to employees
    employees: HasMany["Employee"] = HasMany(
        foreign_key="department_id",
        inverse_of="department"
    )


class Author(ActiveRecord):
    name: str

    # Relations
    books: HasMany["Book"] = HasMany(
        foreign_key="author_id",
        inverse_of="author"
    )
    profile: HasOne["Profile"] = HasOne(
        foreign_key="author_id",
        inverse_of="author"
    )


class Book(ActiveRecord):
    title: str
    author_id: int

    # Relations
    author: BelongsTo["Author"] = BelongsTo(
        foreign_key="author_id",
        inverse_of="books"
    )
    chapters: HasMany["Chapter"] = HasMany(
        foreign_key="book_id",
        inverse_of="book"
    )


class Chapter(ActiveRecord):
    title: str
    book_id: int

    # Relations
    book: BelongsTo["Book"] = BelongsTo(
        foreign_key="book_id",
        inverse_of="chapters"
    )


class Profile(ActiveRecord):
    bio: str
    author_id: int

    # Relations
    author: BelongsTo["Author"] = BelongsTo(
        foreign_key="author_id",
        inverse_of="profile"
    )
