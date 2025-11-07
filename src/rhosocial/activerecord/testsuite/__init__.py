# src/rhosocial/activerecord/testsuite/__init__.py
"""RhoSocial ActiveRecord Test Suite

The version number for this package follows the same naming rules as the main 
rhosocial-activerecord package, but with a key difference:

- Major and minor version numbers (e.g., 1.0 in 1.0.x) are kept consistent with 
  the main rhosocial-activerecord package to indicate compatibility
- Patch and subsequent optional parts (e.g., .0.dev11 in 1.0.0.dev11) evolve 
  independently to allow for independent development cycles

This allows the test suite to maintain compatibility with the main package 
while being developed and released on its own schedule.
"""

# __version__ is now defined in pyproject.toml