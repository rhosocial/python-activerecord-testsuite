"""Shared FastAPI app factory for database benchmark scenarios."""

from typing import Any, Callable, List, Type

from fastapi import FastAPI, HTTPException, Query, status

from .schemas import HealthResponse, TransactionalUpdatePayload, UserCreate, UserResponse


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

    @app.get("/users/by-email/{email}", response_model=UserResponse)
    async def get_user_by_email(email: str):
        async with backend_context_factory():
            users = await model_class.query().where(model_class.c.email == email).limit(1).all()
        if not users:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return _to_response(users[0])

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

    @app.post("/users/{user_id}/transactional-update", response_model=UserResponse)
    async def transactional_update_user(user_id: int, payload: TransactionalUpdatePayload):
        async with backend_context_factory():
            user = await model_class.find_one(user_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            user.username = payload.phase_1
            rows = await user.save()
            if rows != 1:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            phase_1_user = await model_class.find_one(user_id)
            if phase_1_user is None or phase_1_user.username != payload.phase_1:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT)
            phase_1_user.username = payload.phase_2
            rows = await phase_1_user.save()
            if rows != 1:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            phase_2_user = await model_class.find_one(user_id)
        if phase_2_user is None or phase_2_user.username != payload.phase_2:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)
        return _to_response(phase_2_user)

    return app
