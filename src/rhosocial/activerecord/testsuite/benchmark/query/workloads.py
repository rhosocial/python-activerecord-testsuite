"""Reusable query benchmark workloads."""

from typing import Any, Type


def filter_order_limit(model_class: Type[Any]) -> list:
    results = (
        model_class.query()
        .where(model_class.c.is_active == True)
        .order_by((model_class.c.age, "DESC"))
        .limit(10)
        .all()
    )
    if len(results) != 10:
        raise AssertionError("filter/order/limit benchmark returned unexpected row count")
    if any(not row.is_active for row in results):
        raise AssertionError("filter/order/limit benchmark returned inactive rows")
    if any(results[index].age < results[index + 1].age for index in range(len(results) - 1)):
        raise AssertionError("filter/order/limit benchmark returned rows in unexpected order")
    return results


async def filter_order_limit_async(model_class: Type[Any]) -> list:
    results = await (
        model_class.query()
        .where(model_class.c.is_active == True)
        .order_by((model_class.c.age, "DESC"))
        .limit(10)
        .all()
    )
    if len(results) != 10:
        raise AssertionError("async filter/order/limit benchmark returned unexpected row count")
    if any(not row.is_active for row in results):
        raise AssertionError("async filter/order/limit benchmark returned inactive rows")
    if any(results[index].age < results[index + 1].age for index in range(len(results) - 1)):
        raise AssertionError("async filter/order/limit benchmark returned rows in unexpected order")
    return results


def count_active(model_class: Type[Any]) -> int:
    count = model_class.query().where(model_class.c.is_active == True).count()
    if count <= 0:
        raise AssertionError("count benchmark returned no active rows")
    return count


async def count_active_async(model_class: Type[Any]) -> int:
    count = await model_class.query().where(model_class.c.is_active == True).count()
    if count <= 0:
        raise AssertionError("async count benchmark returned no active rows")
    return count
