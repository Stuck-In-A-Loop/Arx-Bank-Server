import asyncio
import json
import datetime
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from arx_bank_server.setup import logger
from arx_bank_server.models import UserModel, get_async_session, UserLogin, User
from arx_bank_server.setup import DetectionStatus
from typing import Annotated
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from .utils import UnauthorizedError, NotFoundError, DetectionData
from arx_bank_server.mail import send_login_email

login_router = APIRouter(prefix="/login", tags=["login"])


@login_router.post(
    "/",
    response_model=UserModel,
    responses={
        404: {"model": NotFoundError},
        401: {"model": UnauthorizedError},
    },
)
async def login(
    request: Request, *, db: Annotated[AsyncSession, Depends(get_async_session)], user: UserLogin
):
    statement = select(User).where(User.email == user.email)
    result = await db.exec(statement)
    user_db = result.first()
    if not user_db:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": "User not found"}
        )
    if user_db.password != user.password:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid password"},
        )
    request.app.state.current_user = UserModel.model_validate(user_db)
    # Send "Login attempt" email
    await send_login_email(
        user_db.email,
        user_db.name,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    return UserModel.model_validate(user_db)


@login_router.get("/status", response_model=DetectionData)
async def send_events(request: Request):
    async def event_stream():
        while True:
            # Fetch the latest data
            detected_users = request.app.state.shared_data.get("users", [])
            count = request.app.state.shared_data.get("count", 0)
            timestamp = request.app.state.shared_data.get("timestamp", 0)
            current_user_face_id = (
                request.app.state.current_user.face_id
                if request.app.state.current_user
                else None
            )

            # Determine status
            if count == 0:
                status = DetectionStatus.NO_USER
            elif count > 1:
                status = DetectionStatus.TOO_MANY_USERS
            elif "unknown" in detected_users:
                status = DetectionStatus.UNKNOWN_USER
            elif (
                current_user_face_id is not None
                and current_user_face_id not in detected_users
            ):
                status = DetectionStatus.WRONG_USER
            else:
                status = DetectionStatus.OK

            # Build the event data
            event_data = {
                "users": detected_users,
                "count": count,
                "timestamp": timestamp,
                "status": status,
            }
            logger.debug("Sending event: %s", event_data)

            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(2)  # Send data every 2 seconds

    return StreamingResponse(event_stream(), media_type="text/event-stream")
