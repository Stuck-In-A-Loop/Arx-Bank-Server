import asyncio
from multiprocessing.managers import DictProxy
import face_recognition
import pickle
import os
from multiprocessing import Queue, Process
import cv2
import time
import numpy as np
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from arx_bank_server.setup import logger, DetectionStatus, settings
from arx_bank_server.models import User, get_async_session_opener
from arx_bank_server.tasks.training_tasks import train_user
from .camera import get_frame_from_queue


def capture_images(frame_queue: Queue, train_state: DictProxy, frame_total: int = 5):
    base_path = "/shared/image_data"
    person_path = os.path.join(base_path, train_state["user_to_train"])
    os.makedirs(person_path, exist_ok=True)

    train_state["position"] = "center"

    while train_state["captured_frames"] < frame_total:
        frame = get_frame_from_queue(frame_queue)
        image_path = os.path.join(person_path, f"{train_state['captured_frames']}.jpg")
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_frame)
        if len(face_locations) == 1:
            cv2.imwrite(image_path, frame)
            train_state["captured_frames"] += 1
            train_state["detection_status"] = DetectionStatus.OK
            logger.info(f"Captured frame {train_state['captured_frames']}")
            time.sleep(1)
        elif len(face_locations) == 0:
            train_state["detection_status"] = DetectionStatus.NO_USER
            logger.debug("No user detected")
            time.sleep(1)
        elif len(face_locations) > 1:
            train_state["detection_status"] = DetectionStatus.TOO_MANY_USERS
            logger.debug("Too many users detected")
            time.sleep(1)

        # capture frame 4 from position left and frame 5 from possition right
        if train_state["captured_frames"] == 3:
            train_state["position"] = "left"
        elif train_state["captured_frames"] == 4:
            train_state["position"] = "right"
        time.sleep(2)
    train_process = Process(target=train, args=(train_state,))
    train_process.start()


async def save_face_data(face_id: str, face_data: bytes):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async with AsyncSession(engine) as session:
        query = select(User).where(User.face_id == face_id)
        user = (await session.exec(query)).first()
        if user:
            user.face_data = face_data
            user.trained = True
            session.add(user)
            await session.commit()
            return True
    await engine.dispose()
    return False


def train(train_state: DictProxy):
    base_path = "image_data"
    person_path = os.path.join(base_path, train_state["user_to_train"])
    if not os.path.isdir(person_path):
        return
    logger.info("Processing %s", train_state["user_to_train"])

    # encodings = []
    # for image_name in os.listdir(person_path):
    #     image_path = os.path.join(person_path, image_name)
    #     image = face_recognition.load_image_file(image_path)
    #     face_enc = face_recognition.face_encodings(image)
    #     if face_enc:  # Ensure encoding was successful
    #         encodings.append(face_enc[0])

    # logger.info("Found %d faces", len(encodings))
    # logger.debug("Known faces: %d", len(train_state["known_faces"]))
    # logger.debug("Known names: %d", len(train_state["known_names"]))
    # if encodings:
    #     avg_encoding = sum(encodings) / len(encodings)  # Average encoding

    #     # Convert DictProxy to regular dictionary
    #     train_state_dict = dict(train_state)

    #     train_state_dict["known_faces"].append(avg_encoding)
    #     train_state_dict["known_names"].append(train_state["user_to_train"])
    #     logger.debug("Encoding: %s", avg_encoding)

    #     # Update the DictProxy object
    #     train_state.update(train_state_dict)

    #     asyncio.run(
    #         save_face_data(train_state["user_to_train"], pickle.dumps(avg_encoding))
    #     )
    train_result = train_user.delay(train_state["user_to_train"])

    result = train_result.get(timeout=300)  # 5-minute timeout
    if result["success"]:
        print(
            f"Training successful for user: {result["success"]}, saving to database..."
        )
        asyncio.run(save_face_data(result["user"], result["encoding"]))
    else:
        print(
            f"Training failed for user: {train_state["user_to_train"]}, reason: {result['message']}"
        )

    # train_state["known_faces"].extend(known_faces)
    # train_state["known_names"].extend(known_names)
    logger.debug("Known faces: %d", len(train_state["known_faces"]))
    logger.debug("Known names: %d", len(train_state["known_names"]))
    # Save encodings to a file
    # with open("face_encodings.pkl", "wb") as f:
    #     pickle.dump(
    #         {
    #             "encodings": train_state["known_faces"],
    #             "names": train_state["known_names"],
    #         },
    #         f,
    #     )
    train_state["train"] = False
    train_state["last_trained"] = train_state["user_to_train"]
    train_state["captured_frames"] = 0
    train_state["position"] = "center"
    train_state["detection_status"] = DetectionStatus.OK
    train_state["user_to_train"] = ""
    logger.info("Training complete")
    # frame_queue.put(None)
    return
