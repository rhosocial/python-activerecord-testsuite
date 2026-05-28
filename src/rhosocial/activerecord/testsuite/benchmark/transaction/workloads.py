"""Reusable transaction benchmark workloads."""

from typing import Any, Dict, List, Type


def bulk_insert_transaction(model_class: Type[Any], payloads: List[Dict[str, object]]) -> list:
    inserted = []
    with model_class.transaction():
        for payload in payloads:
            instance = model_class(**payload)
            rows = instance.save()
            if rows != 1 or instance.id is None:
                raise AssertionError("transaction benchmark did not persist a row")
            inserted.append(instance)
    for instance in inserted:
        found = model_class.find_one(instance.id)
        if found is None or found.username != instance.username:
            raise AssertionError("transaction benchmark committed unexpected data")
    return inserted


async def bulk_insert_transaction_async(
    model_class: Type[Any], payloads: List[Dict[str, object]]
) -> list:
    inserted = []
    async with model_class.transaction():
        for payload in payloads:
            instance = model_class(**payload)
            rows = await instance.save()
            if rows != 1 or instance.id is None:
                raise AssertionError("async transaction benchmark did not persist a row")
            inserted.append(instance)
    for instance in inserted:
        found = await model_class.find_one(instance.id)
        if found is None or found.username != instance.username:
            raise AssertionError("async transaction benchmark committed unexpected data")
    return inserted
