"""Reusable mixin benchmark workloads."""

from typing import Any, Dict, Type


def timestamp_insert(model_class: Type[Any], payload: Dict[str, object]) -> Any:
    instance = model_class(**payload)
    rows = instance.save()
    if rows != 1 or instance.id is None:
        raise AssertionError("timestamp insert benchmark did not persist exactly one row")
    if instance.created_at is None or instance.updated_at is None:
        raise AssertionError("timestamp insert benchmark did not populate timestamps")
    return instance


async def timestamp_insert_async(model_class: Type[Any], payload: Dict[str, object]) -> Any:
    instance = model_class(**payload)
    rows = await instance.save()
    if rows != 1 or instance.id is None:
        raise AssertionError("async timestamp insert benchmark did not persist exactly one row")
    if instance.created_at is None or instance.updated_at is None:
        raise AssertionError("async timestamp insert benchmark did not populate timestamps")
    return instance


def timestamp_update(model_class: Type[Any], record_id: Any, suffix: str) -> Any:
    instance = model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("timestamp update benchmark could not find seed row")
    original_created_at = instance.created_at
    original_updated_at = instance.updated_at
    instance.username = f"bench_timestamp_{suffix}"
    rows = instance.save()
    if rows != 1:
        raise AssertionError("timestamp update benchmark did not update exactly one row")
    instance.refresh()
    if instance.created_at != original_created_at:
        raise AssertionError("timestamp update benchmark changed created_at")
    if instance.updated_at is None or instance.updated_at < original_updated_at:
        raise AssertionError("timestamp update benchmark did not refresh updated_at")
    return instance


async def timestamp_update_async(model_class: Type[Any], record_id: Any, suffix: str) -> Any:
    instance = await model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("async timestamp update benchmark could not find seed row")
    original_created_at = instance.created_at
    original_updated_at = instance.updated_at
    instance.username = f"bench_timestamp_{suffix}"
    rows = await instance.save()
    if rows != 1:
        raise AssertionError("async timestamp update benchmark did not update exactly one row")
    await instance.refresh()
    if instance.created_at != original_created_at:
        raise AssertionError("async timestamp update benchmark changed created_at")
    if instance.updated_at is None or instance.updated_at < original_updated_at:
        raise AssertionError("async timestamp update benchmark did not refresh updated_at")
    return instance
