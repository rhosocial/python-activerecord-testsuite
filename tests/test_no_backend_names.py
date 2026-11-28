# tests/test_no_backend_names.py
"""The rule tree knows no concrete backend.

This repository defines what a backend must satisfy; the rules are not written
from any backend's point of view. The moment a name appears in them -- in an
assertion, a fixture, a probe, a docstring -- the rule has acquired a favourite,
and three things follow:

* a new backend finds rules written around someone else's spelling, and the
  reader cannot tell which parts are contract and which are that backend's
  habit;
* a backend-specific expectation looks like a contract, so a backend that does
  not satisfy it is judged against a rule the framework never stated;
* the list of backends becomes something this repository must maintain, which is
  exactly the coupling the split exists to prevent.

So the ban is total within the rule tree, casing included: a check that only
caught ``mysql`` would be defeated by ``MySQL`` in the next sentence.

Scope, and why it is the rule tree only
---------------------------------------
The scan covers ``src/rhosocial/activerecord/testsuite/feature/rules/`` -- the
part that states what a backend must satisfy. The rest of this repository has a
backlog of prose that predates the rule; that backlog is not swept here, because
a guard that cannot pass teaches people to weaken it. Fixing the backlog is its
own change; until then this guard protects the increments, which is where the
rule is actually being written.

The checker itself is outside the scanned tree, so it needs no exemption. That
is deliberate: an allowlist would be the first thing to grow.

How to satisfy it
-----------------
Write the rule, not the backend. ``<backend>``, ``the backend under test`` and
``a provider`` are accurate; a probe uses a made-up owner (``ProbeThing``,
``prefix="Probe"``) rather than borrowing a real one, because a probe that reuses
a backend's name quietly reintroduces the knowledge it was meant to avoid.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOT = REPO_ROOT / "src/rhosocial/activerecord/testsuite/feature/rules"

#: Directories that hold tooling or caches rather than content. A byte-compiled
#: module is not a sentence anybody wrote for a reader.
SKIPPED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
}

#: Binary payloads: no words to judge. Everything else is read as text, including
#: files with no extension, so a stray note cannot escape the ban by being
#: unlabelled.
SKIPPED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".so",
    ".pyd",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".whl",
}

#: The names a concrete backend answers to. Built as data rather than as a
#: literal per backend; the scanner lowercases both sides, which is what makes
#: casing irrelevant.
BACKEND_NAMES = (
    "mysql",
    "mariadb",
    "postgres",
    "pgsql",
    "sqlite",
    "oracle",
    "sqlserver",
    "mssql",
    "snowflake",
    "clickhouse",
    "bigquery",
    "firebird",
)

_TOKEN_RE = re.compile("|".join(sorted(BACKEND_NAMES, key=len, reverse=True)), re.IGNORECASE)


def _skipped(path: Path) -> bool:
    """Whether this path is tooling or a binary rather than content."""
    parts = set(path.parts)
    if parts & SKIPPED_DIRS:
        return True
    return path.suffix.lower() in SKIPPED_SUFFIXES


def _files():
    """Every content file of the rule tree."""
    for current, dirs, files in os.walk(SCAN_ROOT):
        dirs[:] = [name for name in dirs if not _skipped(Path(current, name))]
        for name in sorted(files):
            path = Path(current, name)
            if not _skipped(path):
                yield path


def _occurrences(path: Path):
    """``(lineno, spelling)`` for each backend name in the file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        for match in _TOKEN_RE.finditer(line):
            yield lineno, match.group(0)


def test_no_backend_name_appears_in_the_rule_tree():
    """No file under the rule tree names a concrete backend.

    A failure is a sentence to rewrite: the name either belongs in the backend
    that owns it, or it was standing in for "the backend under test" and should
    say so. A probe uses a made-up owner for the same reason.
    """
    offenders = []
    for path in _files():
        for lineno, spelling in _occurrences(path):
            offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: {spelling}")
    assert not offenders, (
        "concrete backend names in the rule tree "
        f"({len(offenders)} occurrences):\n" + "\n".join(offenders)
    )


# ---- synthetic controls ------------------------------------------------- #

#: The rule tree holds a handful of files; the floor is below that count so
#: ordinary edits do not trip it, while a mis-rooted walk still fails here
#: instead of passing on an empty offender list.
MIN_FILES = 5


def test_the_scan_sees_the_rule_tree() -> None:
    """The walk must reach real content, or an empty offender list means nothing."""
    scanned = list(_files())
    assert len(scanned) >= MIN_FILES, f"only {len(scanned)} files were scanned"


def test_a_backend_name_in_a_docstring_is_flagged(tmp_path: Path) -> None:
    sample = tmp_path / "rule.py"
    sample.write_text('"""The MySql rule."""\n', encoding="utf-8")
    spellings = [spelling for _, spelling in _occurrences(sample)]
    assert spellings, "a mixed-case name in a docstring was not reported"


def test_a_backend_name_in_a_probe_is_flagged(tmp_path: Path) -> None:
    sample = tmp_path / "probe.py"
    sample.write_text('PREFIX = "Postgres"\n', encoding="utf-8")
    assert list(_occurrences(sample)), "a name used as probe data was not reported"


def test_a_neutral_sentence_is_clean(tmp_path: Path) -> None:
    sample = tmp_path / "rule.py"
    sample.write_text('SCENARIO = "<backend>_memory"\nPREFIX = "Probe"\n', encoding="utf-8")
    assert not list(_occurrences(sample))
