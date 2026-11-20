# src/rhosocial/activerecord/testsuite/feature/basic/fixtures/test_version_probes.py
"""``resolve()`` selects the correct version file for every typing probe.

Probe names are unique per version file, so the module a resolved probe was
defined in proves which file the running interpreter selected.  The "newest
required <= current" rule is checked directly as well: it is what makes 3.13
land on 3.12 and 3.15 land on 3.14 even though neither has a file of its own.
"""

import sys

import pytest

from rhosocial.activerecord.testsuite.feature.basic import fixtures
from rhosocial.activerecord.testsuite.feature.basic.fixtures import models as baseline

PROBE_SUFFIXES = ("39", "310", "311", "312", "314")


class TestVersionProbeResolution:
    """Version-gated resolution of the typing probes in ``fixtures/``."""

    def test_version_modules_are_ordered_newest_first(self):
        assert fixtures.VERSION_MODULES == (
            ("314", (3, 14)),
            ("312", (3, 12)),
            ("311", (3, 11)),
            ("310", (3, 10)),
            ("39", (3, 9)),
        )

    @pytest.mark.parametrize("suffix", PROBE_SUFFIXES)
    def test_probe_resolves_to_its_own_version_file(self, suffix):
        required = dict(fixtures.VERSION_MODULES)[suffix]
        if sys.version_info[:2] < required:
            pytest.skip(f"probe {suffix} needs Python {required[0]}.{required[1]}+")

        probe = fixtures.resolve(f"TypingProbe{suffix}")

        assert probe.__module__.endswith(f".models_py{suffix}")

    def test_newest_available_probe_matches_the_interpreter(self):
        current = sys.version_info[:2]
        expected = next(
            (suffix for suffix, required in fixtures.VERSION_MODULES if current >= required),
            None,
        )
        if expected is None:
            pytest.skip("interpreter predates every version probe")

        probe = fixtures.resolve(f"TypingProbe{expected}")

        assert probe.__module__.endswith(f".models_py{expected}")

    def test_non_probe_names_fall_back_to_the_baseline(self):
        assert fixtures.resolve("User") is baseline.User

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="PEP 649 needs Python 3.14+")
    def test_314_probe_uses_lazy_annotations(self):
        from typing import get_type_hints

        probe = fixtures.resolve("TypingProbe314")

        assert hasattr(probe, "__annotate__")
        assert get_type_hints(probe)["peer"].__name__ == "ProbePeer314"
