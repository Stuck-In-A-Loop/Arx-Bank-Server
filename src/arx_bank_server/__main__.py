from typing import Union
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing import Process, Queue, Manager
import cv2
import alembic.config

from arx_bank_server.setup import logger
from arx_bank_server.setup import settings, DetectionStatus
from arx_bank_server.models import create_init_user, run_migrations
from arx_bank_server.camera import camera_frames, process_faces
from arx_bank_server.routers import (
    camera_router,
    healthcheck_router,
    login_router,
    register_router,
)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    try:
        logger.info(f"Starting {settings.PROJECT_NAME}...")
        # alembicArgs = [
        #     "--raiseerr",
        #     "upgrade",
        #     "head",
        # ]
        # alembic.config.main(argv=alembicArgs)
        await run_migrations()
        await create_init_user()
        manager = Manager()
        shared_data = manager.dict({"users": [], "count": 0, "timestamp": 0})
        train_state = manager.dict(
            {
                "train": False,
                "user_to_train": "",
                "last_trained": "",
                "captured_frames": 0,
                "position": "center",
                "detection_status": DetectionStatus.OK,
                "known_faces": [],
                "known_names": [],
            }
        )
        frame_queue: Queue = Queue(maxsize=10)  # Shared queue
        process_queue: Queue = Queue(maxsize=10)  # Shared queue
        # camera_process = Process(
        #     target=camera_frames,
        #     args=(frame_queue, process_queue),
        # )
        # camera_process.start()
        process_faces_process = Process(
            target=process_faces, args=(process_queue, shared_data, train_state)
        )
        process_faces_process.start()
        # app_instance.state.camera_process = camera_process
        app_instance.state.process_faces_process = process_faces_process
        app_instance.state.frame_queue = frame_queue
        app_instance.state.process_queue = process_queue
        app_instance.state.shared_data = shared_data
        app_instance.state.train_state = train_state

        app_instance.state.current_user = None

        yield

        cv2.destroyAllWindows()

        # camera_process.terminate()
        # camera_process.join()
        process_faces_process.terminate()
        process_faces_process.join()
    finally:
        logger.info(f"Stopping {settings.PROJECT_NAME}...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

if settings.BACKEND_CORS_ORIGINS:
    logger.info("CORS origins: %s", settings.BACKEND_CORS_ORIGINS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def read_root():
    return {"Hello": "World"}


app.include_router(camera_router)
app.include_router(healthcheck_router)
app.include_router(login_router)
app.include_router(register_router)
