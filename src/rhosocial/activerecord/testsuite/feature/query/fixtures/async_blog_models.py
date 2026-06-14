# src/rhosocial/activerecord/testsuite/feature/query/fixtures/async_blog_models.py
"""Async blog model fixtures — re-exports from async_models.

NOTE: AsyncPost and AsyncComment are now defined in async_models.py alongside
AsyncUser so that forward references ('AsyncPost', 'AsyncComment') declared
on AsyncUser can be resolved at runtime.  This file remains as a backward-
compatible re-export shim so that existing provider imports do not break.
"""
from .async_models import AsyncUser, AsyncPost, AsyncComment  # noqa: F401