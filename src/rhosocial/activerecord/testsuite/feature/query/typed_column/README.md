# The typed-column contracts, and how to satisfy them in a backend

This directory holds the cross-backend contracts of the typed-column work:

* ``test_typed_column_contracts.py`` — the column-expression layer: an
  explicit ``UseColumnType`` declaration means the same class on every
  backend, inference follows each backend's own ``suggested_column_types()``
  table, narrowing is real, rendering does not depend on the column class,
  and JSON paths are built identically everywhere.
* ``test_protocol_guarantees.py`` — the protocol's own claims, asserted per
  backend: every common entry is answered (a class or an explicit ``None``),
  the table's answers stay class-or-``None``, the column object has no slot
  for a field's DataType and carries no value-family label, and an annotation
  outside the vocabulary fails naming ``UseColumnType`` rather than falling
  back to a universal column.
* ``column_helpers.py`` — the test-side helper that mirrors the field
  accessor's selection step, plus the canonical ``COMMON_TYPES`` list the
  completeness contract holds each backend to.
* ``test_enum_capability_contracts.py`` / ``test_uuid_capability_contracts.py``
  — the concept-specific capability contracts (enum storage, UUID storage).

A backend satisfies these through the dialect's own declarations, not by
editing anything here. The rules below are the discipline the nine backends
converged on; each backend's local plan directory
(``.claude/plan/<date>/`` in that backend's repository) records the
repository-specific history behind them.

## The three-list discipline (expression round-trip matrix)

Every backend's round-trip matrix keeps three lists, and the two integrity
tests pin them **in both directions**: what is named is real, and what is
real is named. An entry that cannot be explained by one of the rules below
is a bug in the lists, not a peculiarity to document and ignore.

1. **Measure with valid arguments before deciding anything.** An invalid
   argument raises the constructor's own validation error and hides the
   dialect's real answer. The recurring example: a UUID constant expression
   probed with an invalid ``which`` raises ``ValueError`` first and reads as
   rescuable, while a *valid* ``which`` reveals the dialect refusing the
   whole concept in ``__init__``. Probe with the argument the constructor
   would accept in a working case.

2. **A class that refuses in ``__init__`` regardless of arguments** goes in
   ``UNCONSTRUCTIBLE``, with a comment stating the measured reason. No
   registered constructor can change that answer, so none is written.

3. **A class a registered special constructor rescues**:
   * renders → register the constructor, and appear in no other list;
   * refuses to render → register the constructor **and** pin the refusal
     in ``LEGITIMATE_NON_RENDERS`` as ``(exception type, message fragment)``.
     The pin now has something to assert against.

4. **Never in two lists at once.** The pin table is consulted before the
   ``UnsupportedFeatureError`` branch, so a pin on an unconstructible class
   asserts a rendering nothing can ever ask for. If a pin and an
   ``UNCONSTRUCTIBLE`` entry name the same class, one of them is wrong.

5. **Version-gated behaviour is not statically pinnable.** The pin table is
   static; a type or refusal that flips with the server version (MariaDB's
   UUID type at 10.7 is the recorded case) fails the pin on one end of the
   version matrix no matter which answer is pinned. Leave it unpinned and
   assert it in a version-parametrised test instead.

6. **The integrity tests fail without naming the offender.** When
   ``test_pinned_non_render_really_does_not_render`` reports
   ``DID NOT RAISE``, run a probe that iterates the pin table and reports
   each entry's actual outcome; do not bisect by hand.

## Measurement discipline

* **Measure, then declare.** Every list entry, pin and constructor cites a
  measurement — a probe against the dialect, or a scenario-server answer.
  Refusals quote the server's own response where one exists (ClickHouse's
  ``Expected one of: ...`` list is the model).
* **Reproduce locally before trusting CI.** CI's ``--log-failed`` output is
  partial: a class that fails may not appear in it. The local run is
  authoritative for *which* classes fail; CI is authoritative for what the
  full suite does in the CI environment.
* **Local scope is bounded** (see the organisation rules): the targeted
  files that changed, not the suite.

## The ``parse_type`` contract (the introspection inverse)

Every dialect implements ``parse_type``; it is also the last member of the
``DataTypeSupport`` protocol, so without it ``parse_data_type_str`` falls
back to a generic ``CustomType`` and the protocol check fails. BigQuery was
the last to gain it (``000b97f``) and documents the shape in full; the rules
that are the same everywhere:

1. **One concept in, one class out**, answered by *storage*. Where a
   backend collapses concepts on the way in (four integer widths stored as
   one integer type), the parse answers with the concept that was **not**
   widened — the class whose rendering is that storage — and re-renders the
   identical string. A narrow declaration reading back as its widened
   concept is the differ reporting a real widening.
2. **Bare-word defaults come from ``type_parameter_defaults()``**, never
   from a number written into the parser.
3. **The spelling that was written is carried** on the instance where the
   concept has more than one; it never takes part in equality.
4. **A word the framework does not model is ``CustomType`` carrying the
   word**, not a guess. A word whose text is not identifier-shaped
   (BigQuery's ``STRUCT<...>``) is refused by the type-name validation
   rather than collapsed to a bare name two different columns would share.
5. **Empty input is a caller error** (``ValueError``), not a type name.

## After a core refactor: the sweep checklist

The rebase that landed this branch taught the hard lessons; they generalise
to any future core change that touches the shared vocabulary:

* **Merge conflicts dimension by dimension.** A block that mixes a
  signature change with an assertion change (SQL Server's ``Table(...)``
  argument with ClickHouse's syntax assertions) takes a piece from each
  side, not one side wholesale. Decide per dimension by reading which name
  the *unchanged* downstream code uses.
* **Auto-merged regions still get swept.** PostgreSQL had sixteen failing
  call sites outside every conflict block because a multi-line argument
  list can wrap the argument the check looks for. Grep by content, not by
  line shape.
* **A signature and a body can both look merged and disagree.** A
  two-state default over a tri-state body passed lint and import on every
  backend; only runtime instantiation caught it. Instantiate representative
  expressions after the merge, not just before commit.
* **A registered constructor with the wrong signature breaks working
  cases** — ``make_instance`` prefers specials and does not fall back.
  Test the constructor by itself before registering it.
* **Read the constructor before wrapping a catalogue object.** DDL targets
  are objects (``Type``, ``Table``, ``MaterializedView``, ``Sequence``);
  the class one backend needed is not the class the next one validates.
* **Check a helper script's exit code before ``git add -A`` and
  ``rebase --continue``.** An unchecked abort once committed conflict
  markers into history.
