from celery import Celery
import face_recognition
import os
import pickle
from arx_bank_server.setup import logger
from arx_bank_server.setup.global_settings import settings

app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL", settings.CELERY_DATABASE_URL),
    backend=os.getenv("CELERY_DATABASE_URL", settings.CELERY_DATABASE_URL),
)


@app.task
def train_user(user_to_train: str, base_path: str = "/shared/image_data"):
    """
    Task to train a user's face encodings.
    """
    person_path = os.path.join(base_path, user_to_train)
    if not os.path.isdir(person_path):
        return {"success": False, "message": "User directory not found"}

    encodings = []
    for image_name in os.listdir(person_path):
        image_path = os.path.join(person_path, image_name)
        image = face_recognition.load_image_file(image_path)
        face_enc = face_recognition.face_encodings(image)
        if face_enc:  # Ensure encoding was successful
            encodings.append(face_enc[0])

    logger.info("Found %d faces", len(encodings))
    if encodings:
        avg_encoding = sum(encodings) / len(encodings)
        return {
            "success": True,
            "user": user_to_train,
            "encoding": pickle.dumps(avg_encoding),
        }

    return {"success": False, "message": "No encodings found"}
