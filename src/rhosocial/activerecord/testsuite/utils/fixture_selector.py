# src/rhosocial/activerecord/testsuite/utils/fixture_selector.py
"""
Environment-aware fixture selection module.

Provides functionality to automatically select the most suitable fixture class
based on the runtime environment.
"""
import sys
from typing import Type


def _check_requirements(cls: Type) -> bool:
    """Check if a class satisfies the current environment requirements.

    Checks the following class attributes:
    - __requires_python__: Minimum Python version requirement, e.g., (3, 10)

    Args:
        cls: The fixture class to check.

    Returns:
        True if all requirements are satisfied, False otherwise.
    """
    # Check Python version requirement
    requires_python = getattr(cls, '__requires_python__', None)
    if requires_python is not None:
        current = sys.version_info[:len(requires_python)]
        if current < requires_python:
            return False

    return True


def select_fixture(*candidates: Type) -> Type:
    """Select the most suitable fixture class for the current environment.

    Candidates are ordered by priority (highest version first). The function
    returns the first class that matches the current environment.
    If no match is found, returns the last candidate (default).

    Args:
        *candidates: Candidate fixture classes, ordered by priority
                     (highest version first).

    Returns:
        The first fixture class that satisfies environment requirements;
        if no match, returns the last candidate (default).

    Raises:
        ValueError: If no candidates are provided.

    Example:
        >>> class BaseFixture:
        ...     pass
        >>> class Py310Fixture(BaseFixture):
        ...     __requires_python__ = (3, 10)
        >>> # In Python 3.10+ environment
        >>> select_fixture(Py310Fixture, BaseFixture)
        <class 'Py310Fixture'>
        >>> # In Python 3.8 environment
        >>> select_fixture(Py310Fixture, BaseFixture)
        <class 'BaseFixture'>
    """
    if not candidates:
        raise ValueError("At least one candidate fixture is required")

    for candidate in candidates:
        if _check_requirements(candidate):
            return candidate

    # Fallback to the last candidate (default)
    return candidates[-1]


__all__ = ['select_fixture']
