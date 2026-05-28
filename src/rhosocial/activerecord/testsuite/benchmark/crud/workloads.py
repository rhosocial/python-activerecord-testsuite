"""Reusable CRUD benchmark workloads."""

from typing import Any, Dict, Type


def insert_one(model_class: Type[Any], payload: Dict[str, object]) -> Any:
    instance = model_class(**payload)
    rows = instance.save()
    if rows != 1 or instance.id is None:
        raise AssertionError("insert benchmark did not persist exactly one row")
    return instance


async def insert_one_async(model_class: Type[Any], payload: Dict[str, object]) -> Any:
    instance = model_class(**payload)
    rows = await instance.save()
    if rows != 1 or instance.id is None:
        raise AssertionError("async insert benchmark did not persist exactly one row")
    return instance


def find_one(model_class: Type[Any], record_id: Any) -> Any:
    found = model_class.find_one(record_id)
    if found is None or found.id != record_id:
        raise AssertionError("find benchmark returned an unexpected row")
    return found


async def find_one_async(model_class: Type[Any], record_id: Any) -> Any:
    found = await model_class.find_one(record_id)
    if found is None or found.id != record_id:
        raise AssertionError("async find benchmark returned an unexpected row")
    return found


def update_one(model_class: Type[Any], record_id: Any, suffix: str) -> Any:
    instance = model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("update benchmark could not find seed row")
    instance.username = f"bench_updated_{suffix}"
    rows = instance.save()
    if rows != 1:
        raise AssertionError("update benchmark did not update exactly one row")
    instance.refresh()
    if instance.username != f"bench_updated_{suffix}":
        raise AssertionError("update benchmark did not persist the expected value")
    return instance


async def update_one_async(model_class: Type[Any], record_id: Any, suffix: str) -> Any:
    instance = await model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("async update benchmark could not find seed row")
    instance.username = f"bench_updated_{suffix}"
    rows = await instance.save()
    if rows != 1:
        raise AssertionError("async update benchmark did not update exactly one row")
    await instance.refresh()
    if instance.username != f"bench_updated_{suffix}":
        raise AssertionError("async update benchmark did not persist the expected value")
    return instance


def delete_one(model_class: Type[Any], record_id: Any) -> None:
    instance = model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("delete benchmark could not find seed row")
    rows = instance.delete()
    if rows != 1:
        raise AssertionError("delete benchmark did not delete exactly one row")
    if model_class.find_one(record_id) is not None:
        raise AssertionError("delete benchmark row still exists")


async def delete_one_async(model_class: Type[Any], record_id: Any) -> None:
    instance = await model_class.find_one(record_id)
    if instance is None:
        raise AssertionError("async delete benchmark could not find seed row")
    rows = await instance.delete()
    if rows != 1:
        raise AssertionError("async delete benchmark did not delete exactly one row")
    if await model_class.find_one(record_id) is not None:
        raise AssertionError("async delete benchmark row still exists")
