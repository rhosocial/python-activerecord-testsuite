# Relation Tests

Tests for the relationship system — descriptors (`BelongsTo`, `HasOne`, `HasMany`), caching,
eager loading, validation, modifiers, derived fields on relations, and integration with other
features.

> **Layout note (2026-11-19):** This topic was moved from `feature/relation/` into
> `feature/query/relation/` and merged with the old `feature/query/relations/` group.
> All import paths now use `rhosocial.activerecord.testsuite.feature.query.relation.*`.
> The old `feature/relation/` source tree remains temporarily and is deleted at cleanup.

## Directory Layout

| Subdirectory | Content |
|-------------|---------|
| `legacy/` | Non-duplicate tests carried over from the old `query/relations/` group — direct unit coverage of `RelationalQueryMixin` internal helpers via `MockQuery`/`DummyBackend` (see "Legacy merge" below) |
| `base/` | Core relation descriptor functionality — initialization, loading, reference resolution, relationship registration, inheritance; `IRelationManagement` interface tests |
| `descriptors/` | Descriptor type tests — `BelongsTo`/`HasOne`/`HasMany` initialization, loader config, cache config, type validation; sync/async compatibility (invalid cross-use raises `TypeError`) |
| `ordering/` | Optional `HasMany(..., order_by=...)` ordering — field-name normalization, direct access, `{relation}_query()`, top-level and nested eager loading, modifier precedence, cache, primary-key tie-breakers, and `order_by=None` plain behavior |
| `eager_loading/` | `with_()` method and `RelationConfig`; deep nested relationship chains (e.g. Author → Book → Chapter); bidirectional consistency; custom loader caching with TTL |
| `cache/` | Cache infrastructure — `CacheConfig`, `GlobalCacheConfig`, `CacheEntry` (expiry/TTL), `RelationCache` (set/get/delete/clear, LRU eviction, disabled mode); cache clearing on `del instance.relation` |
| `modifiers/` | Modifier targeting (leaf-only), override semantics, application on nested paths; warning logging on modifier override |
| `validation/` | `RelationshipValidator` / `AsyncRelationshipValidator` — valid and invalid `BelongsTo↔HasMany`/`HasOne` pairings, `inverse_of` auto-set, missing `inverse_of` detection; path validation (empty, leading/trailing dots raise `InvalidRelationPathError`) |
| `derived/` | Derived fields on relation models — basic (`display_name`, `title_length`, `hotness`) and JSON-backed (`language`, `theme`, `tags`) |
| `integration/` | Multi-feature integration — relations with derived fields, `FieldProxy`, and JSON derived fields |
| `boundary/` | Edge cases — null FK, orphan records (missing target), no matching children; `BelongsTo`/`HasOne`/`HasMany` descriptor behavior under these conditions |
| `fixtures/` | Model class definitions (`User`, `Post`, `Comment`, `Employee`, `Department`, `Profile`, `Book`, `Chapter`, `Author`) across 4 Python versions |

## Provider Interface

`interfaces.py` defines `RelationProviderBase`. Backends implement `get_test_scenarios()` and
supply model classes plus dataset loading methods (`load_relation_boundary_dataset()`,
`load_cache_fixture_dataset()`, etc.).

## Legacy merge (old `query/relations/` → `legacy/`)

The old `query/relations/` group held 7 files (`test_relations_basic*`,
`test_relations_with*`, `test_relational_validation*`, plus its `conftest.py`). Each file's
intent was compared against the existing relation subtopics; the outcome:

**Kept (moved to `legacy/`):**

- `test_relational_validation.py` / `test_relational_validation_async.py` — the bulk of these
  files directly exercise `RelationalQueryMixin`'s internal helper methods
  (`_validate_relation_exists`, `_validate_complete_relation_path`, `_process_relation_path`,
  `_add_relation_config`, `_update_existing_relation_config`, `_parse_relation_arg`,
  `_get_next_level_parts`, `_should_update_nested_relation`, `_determine_modifier`, …) with a
  `MockQuery` backed by `DummyBackend`. No equivalent existed in `relation/validation/`, which
  tests the public `with_()` path on a real ActiveQuery. These tests need no database fixtures.
  The per-method exact duplicates listed below were removed from these two files before keeping.

**Dropped as exact/near-exact duplicates (not carried over):**

- `test_relational_validation*.py` — the 11 path-validation methods
  `test_validate_relation_path_{empty_string,leading_dot,trailing_dot,consecutive_dots}`,
  `test_validate_relation_exists_relation_not_found`,
  `test_with_method_invalid_paths{,_leading_dot,_trailing_dot,_consecutive_dots}`,
  `test_with_method_relation_not_found`, and `test_process_relation_path_invalid_format`.
  All assert the same error/messages already covered by
  `validation/test_path_validation.py` (`TestInvalidRelationPath`,
  `TestRelationNotFound`) via the public `with_()` API.
- `test_relations_basic.py` / `test_relations_basic_async.py` — every test duplicates a
  relation-topic test: required/param types → `descriptors/test_descriptors.py`
  (`test_descriptor_foreign_key_type_error`, `test_descriptor_cache_config_type_error`);
  inheritance → `base/test_base.py::test_relation_inheritance`; registration / descriptor
  init / cache management → `base/test_base.py` (`test_relation_descriptor_init`,
  `test_relation_registration_validation`, `test_relation_descriptor_cache_clear`);
  `BelongsTo`/`HasMany`/`HasOne`, multiple relations, `inverse_of`, and query-method generation
  → `descriptors/test_descriptors.py` and `base/test_base.py`.
- `test_relations_with.py` / `test_relations_with_async.py` — `with_()` eager-load config is
  covered by `eager_loading/test_with_method.py`; nested/modifier/duplicate/chained/deep-nesting
  cases by `modifiers/test_modifier_behavior.py` and
  `eager_loading/test_nested_relationship_access.py`; path-validation cases by
  `validation/test_path_validation.py`. The remaining cases use query-layer `order_fixtures` /
  `blog_fixtures` / `combined_fixtures` and add no new relation assertion.
- `query/relations/conftest.py` — its 5-table schema duplicated the fixture set now owned by
  the query topic; the kept legacy tests need no database fixtures.
