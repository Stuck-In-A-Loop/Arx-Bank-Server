import asyncio
import datetime
import json
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from arx_bank_server.models import get_async_session
from arx_bank_server.setup import logger
from arx_bank_server.models import UserModel, UserLogin, User, UserCreate
from arx_bank_server.setup import DetectionStatus
from arx_bank_server.camera import capture_images
from typing import Annotated
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from .utils import (
    AlreadyExistsError,
    NotFoundError,
    RegisteringData,
    TrainResponse,
)
from multiprocessing import Process
from arx_bank_server.mail import send_register_email
from sqlalchemy.exc import IntegrityError

register_router = APIRouter(prefix="/register", tags=["register"])


@register_router.post(
    "/",
    response_model=UserModel,
    responses={
        409: {"model": AlreadyExistsError},
    },
)
async def register(
    request: Request,
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: UserCreate,
):
    statement = select(User).where(User.email == user.email)
    result = await db.exec(statement)
    user_db = result.first()
    if user_db:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User already exists"},
        )
    face_id = user.name.strip().replace(" ", "").lower()
    user.face_id = face_id
    user_db = User(**user.model_dump())
    try:
        db.add(user_db)
        await db.commit()
        await db.refresh(user_db)
    except IntegrityError as e:
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User with the same name already exists"},
        )
    request.app.state.train_state["train"] = True
    request.app.state.train_state["user_to_train"] = user_db.face_id
    # Send "Registration attempt" email
    await send_register_email(user_db.email, user_db.name)
    return UserModel.model_validate(user_db)


@register_router.get("/status", response_model=RegisteringData)
async def send_events(request: Request):
    async def event_stream():
        while True:
            # Fetch the latest data
            frame_captured = request.app.state.train_state.get("captured_frames", 0)
            status = request.app.state.train_state.get(
                "detection_status", DetectionStatus.OK
            )
            position = request.app.state.train_state.get("position", "center")
            frame_total = 5
            event_data = {
                "position": position,
                "frame_captured": frame_captured,
                "frame_total": frame_total,
                "status": status,
            }
            logger.debug("Sending event: %s", event_data)
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(1)

    capture_process = Process(
        target=capture_images,
        args=(request.app.state.frame_queue, request.app.state.train_state, 5),
    )
    capture_process.start()
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@register_router.get(
    "/train/status",
    response_model=TrainResponse,
    responses={404: {"model": NotFoundError}},
)
async def train_status(
    request: Request,
    face_id: str,
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    statement = select(User).where(User.face_id == face_id)
    result = await db.exec(statement)
    user_db = result.first()
    if user_db:
        return JSONResponse(
            content={
                "status": "done" if user_db.trained else "pending",
                "user": (user_db.face_id),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "User not found"},
    )
