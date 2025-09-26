# src/rhosocial/activerecord/testsuite/feature/query/fixtures/models.py
"""
This module defines the generic models used by the query feature tests in the 
testsuite. These models are then configured with specific backends by the
provider implementations in each backend package.
"""
import re
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field

from rhosocial.activerecord import ActiveRecord
from rhosocial.activerecord.field import IntegerPKMixin, TimestampMixin


class QueryTestModel(IntegerPKMixin, TimestampMixin, ActiveRecord):
    """
    A generic model for testing query functionality.
    This model is configured with a specific backend in the provider implementation.
    """
    __table_name__ = "query_test_models"

    # The IntegerPKMixin is expected to handle the `id` field.
    id: Optional[int] = None
    title: str = Field(default="Test Title")
    content: str
    is_active: bool = True
    score: float = 0.0
    # TimestampMixin provides created_at and updated_at