"""Shared FastAPI app factory for database benchmark scenarios."""

from typing import Any, Callable, List, Type

from fastapi import FastAPI, HTTPException, Query, status

from .schemas import HealthResponse, UserCreate, UserResponse


def _to_response(user: Any) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        age=user.age,
        balance=float(user.balance),
        notes=user.notes,
        is_active=bool(user.is_active),
    )


def create_fastapi_benchmark_app(
    model_class: Type[Any],
    backend_context_factory: Callable[[], Any],
    backend_name: str,
    scenario: str,
) -> FastAPI:
    app = FastAPI()

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(ok=True, backend=backend_name, scenario=scenario)

    @app.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(user_id: int):
        async with backend_context_factory():
            user = await model_class.find_one(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return _to_response(user)

    @app.get("/users", response_model=List[UserResponse])
    async def list_users(limit: int = Query(default=20, ge=1)):
        async with backend_context_factory():
            users = await model_class.query().limit(limit).all()
        return [_to_response(user) for user in users]

    @app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def create_user(payload: UserCreate):
        async with backend_context_factory():
            user = model_class(**payload.model_dump())
            rows = await user.save()
        if rows != 1 or user.id is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return _to_response(user)

    return app
