"""HTTP workloads for FastAPI benchmark scenarios."""

import asyncio

from rhosocial.activerecord.testsuite.benchmark.fastapi.interfaces import (
    FASTAPI_DEFAULT_CONCURRENCY,
    FASTAPI_DEFAULT_REPEAT,
)


async def health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    return data


async def get_user(client, record_id):
    response = await client.get(f"/users/{record_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == record_id
    return data


async def get_user_by_email(client, payload):
    response = await client.get(f"/users/by-email/{payload['email']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    return data


async def list_users(client, limit: int):
    response = await client.get("/users", params={"limit": limit})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= limit
    return data


async def create_user(client, payload):
    response = await client.post("/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    return data


async def concurrent_get_users_by_email(context):
    payloads = context.payloads
    assert payloads
    concurrency = getattr(context, "concurrency", FASTAPI_DEFAULT_CONCURRENCY)
    repeat = getattr(context, "repeat", FASTAPI_DEFAULT_REPEAT)

    async def request_one(index):
        payload = payloads[index % len(payloads)]
        return await get_user_by_email(context.client, payload)

    results = []
    for iteration in range(repeat):
        offset = iteration * concurrency
        batch = await asyncio.gather(
            *(request_one(offset + index) for index in range(concurrency))
        )
        results.extend(batch)
    return {
        "backend": context.backend_name,
        "scenario": context.scenario,
        "connection_strategy": context.connection_strategy,
        "requests": len(results),
        "unique_emails": len({result["email"] for result in results}),
    }


async def concurrent_transactional_updates(context):
    assert context.record_ids
    concurrency = getattr(context, "concurrency", FASTAPI_DEFAULT_CONCURRENCY)
    repeat = getattr(context, "repeat", FASTAPI_DEFAULT_REPEAT)
    workers = min(concurrency, len(context.record_ids))

    async def update_worker(worker):
        user_id = context.record_ids[worker]
        final_name = None
        for iteration in range(repeat):
            phase_1 = f"phase-1-{worker}-{iteration}"
            phase_2 = f"phase-2-{worker}-{iteration}"
            response = await context.client.post(
                f"/users/{user_id}/transactional-update",
                json={"phase_1": phase_1, "phase_2": phase_2},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == user_id
            assert data["username"] == phase_2
            final_name = phase_2
        final_response = await context.client.get(f"/users/{user_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data["id"] == user_id
        assert final_data["username"] == final_name
        return final_data

    results = await asyncio.gather(*(update_worker(worker) for worker in range(workers)))
    return {
        "backend": context.backend_name,
        "scenario": context.scenario,
        "connection_strategy": context.connection_strategy,
        "requests": workers * repeat,
        "workers": workers,
        "final_ids": [result["id"] for result in results],
    }
