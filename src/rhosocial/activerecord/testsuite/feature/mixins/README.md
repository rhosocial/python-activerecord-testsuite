# Mixin Tests

Tests for built-in model mixins — timestamp tracking, soft delete, and optimistic locking, both
individually and in combination.

## Directory Layout

| File | Description |
|------|-------------|
| `conftest.py` | Scenario parameterization via `IMixinsSyncProvider` / `IMixinsAsyncProvider` |
| `interfaces.py` | `MixinsProviderBase` — requires `timestamped_post_model`, `task_model`, `versioned_product_model`, `combined_article_model` |
| `fixtures/models.py` | Model definitions (`TimestampedPost`, `Task`, `VersionedProduct`, `CombinedArticle`) across 4 Python versions |

### Test Files

| File | Sync/Async | Scope |
|------|------------|-------|
| `test_timestamps.py` | both | `DefaultTimestampMixin` — `created_at` / `updated_at` auto-set and update, timezone handling |
| `test_soft_delete.py` | both | `DefaultSoftDeleteMixin` — `deleted_at` timestamp, `delete()` behavior, query filtering |
| `test_optimistic_lock.py` | both | `DefaultOptimisticLockMixin` — version increment, `DatabaseError` on concurrent conflict |
| `test_combined_articles.py` | both | All three mixins combined on one model — verify coordinated behavior on update, delete, and query |
