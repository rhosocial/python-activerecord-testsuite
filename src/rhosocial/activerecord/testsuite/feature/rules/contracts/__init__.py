# src/rhosocial/activerecord/testsuite/feature/rules/contracts/__init__.py
"""Rule logic shared by the generic layer and every concrete backend.

The distinction these modules are built on: a *rule* is a statement about a
namespace, and a *subject* says which namespace is being examined. A concrete
backend and core's generic layer are two subjects of the same rules -- the
expression package, the naming claim, the openness of a package root -- and the
differences between them are field values, not separate implementations.

* ``subject`` -- what is being examined: which trees belong to it, which
  directory inside them is the expression namespace, whether it carries a name
  prefix, which vocabulary it must not reuse, which package root must stay open.
* ``naming`` -- the rules about where a node lives and what it may be called.

A backend declares its subject in its own conftest and imports the test
functions unchanged. Core declares its own subject in core's test tree, the
same way. Neither side rewrites an assertion.
"""
