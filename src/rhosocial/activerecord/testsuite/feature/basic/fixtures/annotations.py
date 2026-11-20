# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/annotations.py
"""Version-independent declaration constants shared by the basic fixtures.

A DDL source is a model class: the constants here are only the annotation
fragments that several model files need, so they are written once. Nothing in
this module is a model and nothing imports one.
"""

from rhosocial.activerecord.backend.expression.statements import (
    ColumnNullableConstraint,
)
from rhosocial.activerecord.base.fields import UseConstraint
from rhosocial.activerecord.base.fields import UseSqlType
from rhosocial.activerecord.backend.expression.types import IntegerType

#: A single-column integer primary key whose value the database generates.
#: ``Optional[int]`` plus the framework default ``pk_auto_generated()`` is the
#: whole declaration.  The DDL derivation turns it into the backend's own
#: mechanism (AUTO_INCREMENT / SERIAL / IDENTITY / rowid), so no mechanism
#: attribute belongs here.
SQL_INT_PK = (UseSqlType(IntegerType()),)

#: A column the hand-written fixture Definition left nullable. The derivation
#: adds NOT NULL to every non-Optional field, so a projection model that omits
#: the field on INSERT needs the old nullability stated explicitly.
SQL_NULLABLE = UseConstraint(ColumnNullableConstraint)

__all__ = ["SQL_INT_PK", "SQL_NULLABLE"]
