# src/rhosocial/activerecord/testsuite/feature/backend/sqlite_features.py
"""SQLite backend feature support implementation."""

from typing import Tuple
from ..features import FeatureSupport, DatabaseFeature


class SQLiteFeatureSupport(FeatureSupport):
    """SQLite backend feature support declaration."""
    
    def __init__(self, version: Tuple[int, int, int]):
        """Initialize with SQLite version.
        
        Args:
            version: SQLite version as (major, minor, patch) tuple
        """
        super().__init__()
        self.version = version
        self._declare_features()
    
    def _declare_features(self):
        """Declare SQLite feature support based on version."""
        # Window functions supported from 3.25.0+
        if self.version >= (3, 25, 0):
            self.supports([
                DatabaseFeature.WINDOW_FUNCTIONS
            ])
        
        # RETURNING clause supported from 3.35.0+
        if self.version >= (3, 35, 0):
            self.supports([
                DatabaseFeature.RETURNING_CLAUSE,
                DatabaseFeature.RETURNING_EXPRESSIONS,
                DatabaseFeature.RETURNING_ALIASES
            ])
        
        # CTEs supported from 3.8.3+
        if self.version >= (3, 8, 3):
            self.supports([
                DatabaseFeature.CTE,
                DatabaseFeature.CTE_IN_DML
            ])
        
        # Recursive CTEs supported from 3.8.3+
        if self.version >= (3, 8, 3):
            self.supports([
                DatabaseFeature.RECURSIVE_CTE
            ])
        
        # Recursive CTEs with compound queries from 3.34.0+
        if self.version >= (3, 34, 0):
            self.supports([
                DatabaseFeature.COMPOUND_RECURSIVE_CTE
            ])
        
        # Materialized CTEs from 3.35.0+
        if self.version >= (3, 35, 0):
            self.supports([
                DatabaseFeature.MATERIALIZED_CTE
            ])
        
        # JSON operations supported from 3.9.0+
        if self.version >= (3, 9, 0):
            self.supports([
                DatabaseFeature.JSON_OPERATIONS
            ])
        
        # JSON arrow operators from 3.38.0+
        if self.version >= (3, 38, 0):
            self.supports([
                DatabaseFeature.JSON_ARROWS
            ])
        
        # Savepoints supported
        self.supports([
            DatabaseFeature.SAVEPOINT
        ])
        
        # Bulk operations (execute_many) supported with fallback
        self.supports([
            DatabaseFeature.BULK_OPERATIONS
        ])
        
        # Note: SQLite does NOT support CUBE, ROLLUP, GROUPING SETS
        # These are intentionally NOT declared as supported