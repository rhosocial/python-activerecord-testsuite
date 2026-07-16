# Relation Tests

Tests for the relationship system — descriptors (`BelongsTo`, `HasOne`, `HasMany`), caching,
eager loading, validation, modifiers, derived fields on relations, and integration with other
features.

## Directory Layout

| Subdirectory | Content |
|-------------|---------|
| `base/` | Core relation descriptor functionality — initialization, loading, reference resolution, relationship registration, inheritance; `IRelationManagement` interface tests |
| `descriptors/` | Descriptor type tests — `BelongsTo`/`HasOne`/`HasMany` initialization, loader config, cache config, type validation; sync/async compatibility (invalid cross-use raises `TypeError`) |
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
