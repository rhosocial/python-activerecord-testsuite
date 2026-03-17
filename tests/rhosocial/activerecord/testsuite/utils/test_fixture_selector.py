# tests/rhosocial/activerecord/testsuite/utils/test_fixture_selector.py
"""
Environment-aware fixture selector tests.
"""
import sys
import pytest
from unittest import mock

from rhosocial.activerecord.testsuite.utils.fixture_selector import (
    select_fixture,
    _check_requirements,
)


class TestCheckRequirements:
    """Tests for _check_requirements function."""

    def test_no_requirements(self):
        """A class with no requirements should always pass the check."""
        class NoReqs:
            pass

        assert _check_requirements(NoReqs) is True

    def test_requires_python_satisfied(self):
        """Should pass when Python version requirement is satisfied."""
        class Py38Req:
            __requires_python__ = (3, 8)

        # Current Python version should be >= 3.8
        assert _check_requirements(Py38Req) is True

    def test_requires_python_not_satisfied(self):
        """Should fail when Python version requirement is not satisfied."""
        class FutureReq:
            __requires_python__ = (99, 99)  # Future version

        assert _check_requirements(FutureReq) is False

    def test_requires_python_exact_match(self):
        """Should pass when Python version matches exactly."""
        current_major = sys.version_info.major
        current_minor = sys.version_info.minor

        class ExactReq:
            __requires_python__ = (current_major, current_minor)

        assert _check_requirements(ExactReq) is True

    def test_requires_python_partial_version(self):
        """Partial version comparison should work correctly."""
        class MajorOnlyReq:
            __requires_python__ = (3,)  # Only requires Python 3

        assert _check_requirements(MajorOnlyReq) is True


class TestSelectFixture:
    """Tests for select_fixture function."""

    def test_single_candidate(self):
        """Should return the single candidate class."""
        class SingleFixture:
            pass

        result = select_fixture(SingleFixture)
        assert result is SingleFixture

    def test_no_requirements_order(self):
        """Should return the first candidate when no requirements exist."""
        class First:
            pass

        class Second:
            pass

        result = select_fixture(First, Second)
        assert result is First

    def test_python_version_selection_higher_first(self):
        """Should correctly select when higher version fixture is first."""
        class BaseFixture:
            pass

        class Py310Fixture:
            __requires_python__ = (3, 10)

        current = sys.version_info[:2]

        if current >= (3, 10):
            # Should select Py310Fixture
            result = select_fixture(Py310Fixture, BaseFixture)
            assert result is Py310Fixture
        else:
            # Should fall back to BaseFixture
            result = select_fixture(Py310Fixture, BaseFixture)
            assert result is BaseFixture

    def test_python_version_selection_base_first(self):
        """Should select base version when it comes first (matches first)."""
        class BaseFixture:
            pass

        class Py310Fixture:
            __requires_python__ = (3, 10)

        # BaseFixture is first, has no requirements, returned immediately
        result = select_fixture(BaseFixture, Py310Fixture)
        assert result is BaseFixture

    def test_fallback_to_last(self):
        """Should fall back to the last candidate when none satisfy requirements."""
        class Future1:
            __requires_python__ = (99, 1)

        class Future2:
            __requires_python__ = (99, 2)

        class Future3:
            __requires_python__ = (99, 3)

        result = select_fixture(Future1, Future2, Future3)
        assert result is Future3  # Falls back to the last one

    def test_multiple_requirements(self):
        """Test selection logic with multiple candidates."""
        class Base:
            pass

        class Py39:
            __requires_python__ = (3, 9)

        class Py310:
            __requires_python__ = (3, 10)

        class Py312:
            __requires_python__ = (3, 12)

        current = sys.version_info[:2]
        result = select_fixture(Py312, Py310, Py39, Base)

        if current >= (3, 12):
            assert result is Py312
        elif current >= (3, 10):
            assert result is Py310
        elif current >= (3, 9):
            assert result is Py39
        else:
            assert result is Base

    def test_empty_candidates_raises_error(self):
        """Should raise an error when no candidates are provided."""
        with pytest.raises(ValueError, match="At least one candidate"):
            select_fixture()

    def test_with_mock_version(self):
        """Test version selection logic using mock."""
        class Base:
            pass

        class Py310:
            __requires_python__ = (3, 10)

        class Py312:
            __requires_python__ = (3, 12)

        # Simulate Python 3.10 environment
        with mock.patch.object(sys, 'version_info', (3, 10, 5)):
            # Py312 not satisfied, should select Py310
            result = select_fixture(Py312, Py310, Base)
            assert result is Py310

        # Simulate Python 3.8 environment
        with mock.patch.object(sys, 'version_info', (3, 8, 10)):
            # Neither Py312 nor Py310 satisfied, should fall back to Base
            result = select_fixture(Py312, Py310, Base)
            assert result is Base

        # Simulate Python 3.12 environment
        with mock.patch.object(sys, 'version_info', (3, 12, 0)):
            # Py312 satisfied, should select it
            result = select_fixture(Py312, Py310, Base)
            assert result is Py312


class TestSelectorIntegration:
    """Integration tests."""

    def test_real_world_scenario(self):
        """Simulate a real-world usage scenario."""
        # Simulate fixture class inheritance
        class TypeCase:
            """Python 3.8+ base version."""
            __table_name__ = "type_cases"

        class TypeCase310(TypeCase):
            """Python 3.10+ version."""
            __requires_python__ = (3, 10)

        class TypeCase312(TypeCase):
            """Python 3.12+ version."""
            __requires_python__ = (3, 12)

        # Order by priority: highest version first
        result = select_fixture(TypeCase312, TypeCase310, TypeCase)

        current = sys.version_info[:2]
        if current >= (3, 12):
            assert result is TypeCase312
        elif current >= (3, 10):
            assert result is TypeCase310
        else:
            assert result is TypeCase
