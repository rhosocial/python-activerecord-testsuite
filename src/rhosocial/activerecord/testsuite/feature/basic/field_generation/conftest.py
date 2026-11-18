# src/rhosocial/activerecord/testsuite/feature/basic/field_generation/conftest.py
"""L2 declaration for ``basic/field_generation`` -- a database-free scope.

The field-generation contracts assert on Python-side value filling and write-set
filtering. They need no connection, no schema and no dialect: the runner is pure
Python. Accordingly this declaration does **not** set ``uses_database``, and this
directory defines no ``database`` / ``schema`` fixtures. The plugin's collection
check fails loudly if a test here ever starts requesting them.
"""

from rhosocial.activerecord.testsuite.pytest_plugin import Declaration

DECLARATION = Declaration(
    parallel=True,
    purpose="ActiveRecord-side field generators: per-operation fill and filter.",
    passes_means="each operation fills declared fields and filters undeclared ones",
    fails_means="a generator leaks a value into the wrong write set",
)
