"""HTTP workloads for FastAPI benchmark scenarios."""


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
