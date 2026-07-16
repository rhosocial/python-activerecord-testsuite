# Backend Feature Support

Backend-specific feature declaration utilities. Unlike other directories here, this is not a test
category — it provides capability-discovery helpers consumed by the testing infrastructure.

| File | Description |
|------|-------------|
| `sqlite_features.py` | `SQLiteFeatureSupport` — declares SQLite database capabilities (window functions, RETURNING, etc.) based on SQLite version. Used by the capability-based test framework to skip tests for unsupported features. |
