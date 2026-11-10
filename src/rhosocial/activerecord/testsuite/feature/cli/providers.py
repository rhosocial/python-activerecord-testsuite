# src/rhosocial/activerecord/testsuite/feature/cli/providers.py
"""Generic CLI providers that delegate to the existing basic and mixins providers."""

import sys
import types
import uuid
from typing import Any

from rhosocial.activerecord.query import AsyncCTEQuery, CTEQuery
from rhosocial.activerecord.testsuite.core.registry import get_provider_registry

from .fixtures import AsyncCLIReadOnlyUser, CLIReadOnlyUser
from .interfaces import ICLIAsyncProvider, ICLISyncProvider

BASIC_SYNC = "feature.basic.IBasicSyncProvider"
BASIC_ASYNC = "feature.basic.IBasicAsyncProvider"
MIXINS_SYNC = "feature.mixins.IMixinsSyncProvider"
MIXINS_ASYNC = "feature.mixins.IMixinsAsyncProvider"


def _assign_backend(target, source) -> None:
    for attr in (
        "__backend__",
        "__connection_config__",
        "__backend_class__",
        "__logging_config__",
    ):
        if hasattr(source, attr):
            setattr(target, attr, getattr(source, attr))


def _add_query_functions(module, user, cte_class) -> None:
    def active_users():
        return user.query().where(user.c.age >= 18)

    def user_union():
        return user.query().where(user.c.age == 20).union(
            user.query().where(user.c.age == 40)
        )

    def user_cte():
        cte = cte_class(user.backend())
        cte.with_cte("cli_users", user.query().where(user.c.age >= 18))
        return cte.from_cte("cli_users")

    module.active_users = active_users
    module.user_union = user_union
    module.user_cte = user_cte


def _build_module(name, user, bulk, read_only, soft, cte_class, validated):
    module = types.ModuleType(name)
    module.User = user
    module.BulkUser = bulk
    module.ReadOnlyUser = read_only
    module.SoftDeleteTask = soft
    module.ValidatedUser = validated
    _add_query_functions(module, user, cte_class)
    sys.modules[name] = module
    return module


class GenericSyncCLIProvider(ICLISyncProvider):
    """Sync CLI provider assembled from the registered basic/mixins providers."""

    def __init__(self):
        self._basic = None
        self._mixins = None

    def _basic_provider(self):
        if self._basic is None:
            registry = get_provider_registry()
            provider_class = registry.get_provider(BASIC_SYNC)
            if provider_class is None:
                raise RuntimeError("No sync basic provider is registered")
            self._basic = provider_class()
        return self._basic

    def _mixins_provider(self):
        if self._mixins is None:
            registry = get_provider_registry()
            provider_class = registry.get_provider(MIXINS_SYNC)
            if provider_class is None:
                return None
            self._mixins = provider_class()
        return self._mixins

    def get_test_scenarios(self):
        return self._basic_provider().get_test_scenarios()

    def setup_cli_models(self, scenario_name: str) -> Any:
        basic = self._basic_provider()
        user = basic.setup_user_model(scenario_name)
        bulk = basic.setup_bulk_user_model(scenario_name)
        validated = basic.setup_validated_user_model(scenario_name)
        mixins = self._mixins_provider()
        soft = None
        if mixins is not None:
            try:
                soft = mixins.setup_task_model(scenario_name)
            except Exception:
                soft = None

        _assign_backend(CLIReadOnlyUser, user)
        module = _build_module(
            "cli_sync_" + uuid.uuid4().hex,
            user,
            bulk,
            CLIReadOnlyUser,
            soft,
            CTEQuery,
            validated,
        )
        prefix = module.__name__
        return types.SimpleNamespace(
            module=module,
            model=f"{prefix}:User",
            bulk_model=f"{prefix}:BulkUser",
            validated_model=f"{prefix}:ValidatedUser",
            read_only_model=f"{prefix}:ReadOnlyUser",
            soft_delete_model=(
                f"{prefix}:SoftDeleteTask" if soft is not None else None
            ),
            query=f"{prefix}:active_users",
            union_query=f"{prefix}:user_union",
            cte_query=f"{prefix}:user_cte",
        )

    def cleanup_after_test(self, scenario_name: str):
        self._basic_provider().cleanup_after_test(scenario_name)
        mixins = self._mixins_provider()
        if mixins is not None:
            mixins.cleanup_after_test(scenario_name)


class GenericAsyncCLIProvider(ICLIAsyncProvider):
    """Async CLI provider assembled from the registered basic/mixins providers."""

    def __init__(self):
        self._basic = None
        self._mixins = None

    def _basic_provider(self):
        if self._basic is None:
            registry = get_provider_registry()
            provider_class = registry.get_provider(BASIC_ASYNC)
            if provider_class is None:
                raise RuntimeError("No async basic provider is registered")
            self._basic = provider_class()
        return self._basic

    def _mixins_provider(self):
        if self._mixins is None:
            registry = get_provider_registry()
            provider_class = registry.get_provider(MIXINS_ASYNC)
            if provider_class is None:
                return None
            self._mixins = provider_class()
        return self._mixins

    def get_test_scenarios(self):
        return self._basic_provider().get_test_scenarios()

    async def setup_cli_models(self, scenario_name: str) -> Any:
        basic = self._basic_provider()
        user = await basic.setup_user_model(scenario_name)
        bulk = await basic.setup_bulk_user_model(scenario_name)
        validated = await basic.setup_validated_user_model(scenario_name)
        mixins = self._mixins_provider()
        soft = None
        if mixins is not None:
            try:
                soft = await mixins.setup_task_model(scenario_name)
            except Exception:
                soft = None

        _assign_backend(AsyncCLIReadOnlyUser, user)
        module = _build_module(
            "cli_async_" + uuid.uuid4().hex,
            user,
            bulk,
            AsyncCLIReadOnlyUser,
            soft,
            AsyncCTEQuery,
            validated,
        )
        prefix = module.__name__
        return types.SimpleNamespace(
            module=module,
            model=f"{prefix}:User",
            bulk_model=f"{prefix}:BulkUser",
            validated_model=f"{prefix}:ValidatedUser",
            read_only_model=f"{prefix}:ReadOnlyUser",
            soft_delete_model=(
                f"{prefix}:SoftDeleteTask" if soft is not None else None
            ),
            query=f"{prefix}:active_users",
            union_query=f"{prefix}:user_union",
            cte_query=f"{prefix}:user_cte",
        )

    async def cleanup_after_test(self, scenario_name: str):
        await self._basic_provider().cleanup_after_test(scenario_name)
        mixins = self._mixins_provider()
        if mixins is not None:
            await mixins.cleanup_after_test(scenario_name)
