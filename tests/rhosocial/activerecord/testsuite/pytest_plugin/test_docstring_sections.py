# tests/rhosocial/activerecord/testsuite/pytest_plugin/test_docstring_sections.py
"""A docstring's ``purpose:`` / ``passes:`` / ``fails:`` sections are read exactly.

The parser is presentation, so it never fails a test; what it must not do is
invent a section out of a line that only looks like one. The recognition rule
is narrow: a known name, then a colon immediately after it, and the rest of the
line as the section's text -- colons included.
"""

from rhosocial.activerecord.testsuite.pytest_plugin.hooks import parse_docstring


def test_summary_is_the_first_unclaimed_line():
    summary, sections = parse_docstring("A summary.\n\nMore prose.\npasses: it works.")
    assert summary == "A summary."
    assert sections["passes"] == "it works."
    # The summary doubles as the purpose when no purpose line was written.
    assert sections["purpose"] == "A summary."


def test_section_names_are_case_insensitive():
    _, sections = parse_docstring("PURPOSE: p\nPASSES: ok\nFails: no")
    assert sections == {"purpose": "p", "passes": "ok", "fails": "no"}


def test_section_body_keeps_colons_after_the_first():
    _, sections = parse_docstring("passes: a: b: c")
    assert sections["passes"] == "a: b: c"


def test_empty_section_body_is_empty_text():
    _, sections = parse_docstring("passes:")
    assert sections["passes"] == ""


def test_body_text_is_stripped_but_taken_after_the_colon():
    _, sections = parse_docstring("purpose:   spaced   ")
    assert sections["purpose"] == "spaced"


def test_a_near_miss_name_is_not_a_section():
    """Only the three names, spelled without a space before the colon."""
    summary, sections = parse_docstring("purposes: nope\npurpose : also nope")
    assert summary == "purposes: nope"
    assert sections == {"purpose": "purposes: nope"}


def test_continuation_lines_join_the_current_section():
    _, sections = parse_docstring("purpose: first\nsecond line\n\npasses: done")
    assert sections["purpose"] == "first second line"
    assert sections["passes"] == "done"


def test_empty_docstring_yields_nothing():
    assert parse_docstring(None) == ("", {})
    assert parse_docstring("") == ("", {})
