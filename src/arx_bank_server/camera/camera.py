from multiprocessing import Queue
from multiprocessing.managers import DictProxy
import pickle
import time
import face_recognition
import cv2
from queue import Empty
import numpy as np
from cv2 import Mat
from cv2.typing import NumPyArrayNumeric
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from sqlmodel import select

from arx_bank_server.models.db import User
from arx_bank_server.setup import logger, settings, get_or_create_event_loop

# from picamera2 import Picamera2


def get_frame_jpg_from_queue(frame_queue: Queue):
    try:
        frame = frame_queue.get(timeout=1)  # Get the latest frame
        _, buffer = cv2.imencode(".jpg", frame)
        return buffer.tobytes()
    except Empty:
        return None
    except Exception as e:
        logger.error("Error: %s", e)
        return None


def get_frame_from_queue(frame_queue: Queue):
    try:
        frame = frame_queue.get(timeout=1)  # Get the latest frame
        return frame
    except Empty:
        return None


def put_frame_in_queues(
    frame: Mat | NumPyArrayNumeric, frame_queue: Queue, process_queue: Queue
):
    if not frame_queue.full():
        frame_queue.put(frame.copy())
    if not process_queue.full():
        process_queue.put(frame.copy())

    # if settings.SHOW_CAMERA:
    #     cv2.imshow("Video", frame)


def camera_frames(frame_queue: Queue, process_queue: Queue):
    # # cam = Picamera2()
    # height = 720
    # width = 960
    # middle = (int(width / 2), int(height / 2))
    # cam.configure(
    #     cam.create_video_configuration(main={"format": "RGB888", "size": (width, height)})
    # )

    # cam.start()

    # Real-time recognition
    cam = cv2.VideoCapture(0)
    while True:
        # frame = cam.capture_array()
        ret, frame = cam.read()
        if not ret:
            continue
        # print(frame.shape)
        if not frame_queue.full():
            frame_queue.put(frame.copy())
        if not process_queue.full():
            process_queue.put(frame.copy())

        if settings.DEV_MODE:
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cam.release()
    cv2.destroyAllWindows()


async def fetch_known_faces():
    """
    Asynchronously fetch known faces from the database and return two lists:
    one for encodings, one for names/IDs.
    """
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    known_faces = []
    known_names = []
    async with AsyncSession(engine) as session:
        query = select(User)
        users = await session.exec(query)
        for user in users:
            if user.face_data is not None:
                known_faces.append(pickle.loads(user.face_data))
                known_names.append(user.face_id)  # or user.name
    await engine.dispose()
    return known_faces, known_names


def process_faces(process_queue: Queue, shared_data: DictProxy, train_state: DictProxy):
    # Load pre-generated encodings
    # with open("face_encodings.pkl", "rb") as f:
    #     data = pickle.load(f)

    # train_state["known_faces"] = data["encodings"]
    # train_state["known_names"] = data["names"]

    # get the data from the database
    # get the event loop if it exists, else create a new one
    loop = get_or_create_event_loop()
    known_faces, known_names = loop.run_until_complete(fetch_known_faces())
    # known_faces, known_names = asyncio.run(fetch_known_faces())
    train_state["known_faces"] = known_faces
    train_state["known_names"] = known_names
    logger.info("Loaded %d known faces", len(known_faces))

    # empty the queue
    # with process_queue.mutex:
    #     process_queue.queue.clear()
    while True:
        if train_state["train"]:
            continue
        frame = get_frame_from_queue(process_queue)
        if frame is None:
            continue
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame, face_locations
        )
        face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)
        # logger.debug("Faces landmarks: %s", face_landmarks_list)

        detected_users = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                train_state["known_faces"], face_encoding, tolerance=0.6
            )
            if True in matches:
                match_index = matches.index(True)
                detected_users.append(train_state["known_names"][match_index])
            else:
                detected_users.append("Unknown")

        # Update the shared data
        shared_data["users"] = detected_users
        logger.debug("Detected users: %s", detected_users)
        shared_data["count"] = len(detected_users)
        logger.debug("Detected count: %d", len(detected_users))
        shared_data["timestamp"] = time.time()


def detect_motion(prev_frame, curr_frame, face_box):
    x, y, w, h = face_box
    face_prev = prev_frame[y : y + h, x : x + w]
    face_curr = curr_frame[y : y + h, x : x + w]

    # Calculate absolute difference
    diff = cv2.absdiff(face_prev, face_curr)
    motion_score = np.sum(diff)

    # Threshold for motion detection
    if motion_score > 1000:  # Adjust threshold based on your setup
        return True
    return False
