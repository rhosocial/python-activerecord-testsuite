# src/rhosocial/activerecord/__init__.py
"""Namespace package for rhosocial ActiveRecord.

This file enables the namespace package functionality that allows multiple
packages (core, mysql, postgresql, testsuite) to contribute to the same
`rhosocial.activerecord` namespace.

The `pkgutil.extend_path` call is crucial for this to work correctly.
"""

# Extend the namespace path to support backend implementations from separate packages
# This is crucial for the distributed backend architecture where each database backend
# (mysql, postgresql, etc.) can be installed independently
__path__ = __import__('pkgutil').extend_path(__path__, __name__)