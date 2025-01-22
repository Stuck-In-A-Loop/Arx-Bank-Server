import asyncio
import base64
import json
from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import StreamingResponse
from arx_bank_server.camera import get_frame_jpg_from_queue, put_frame_in_queues
from arx_bank_server.setup import logger
import numpy as np
import cv2

camera_router = APIRouter(prefix="/camera", tags=["camera"])


@camera_router.get("/video_feed")
async def video_feed(request: Request) -> StreamingResponse:
    async def frame_generator():
        while True:
            try:
                frame = get_frame_jpg_from_queue(request.app.state.frame_queue)
                if frame:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    )
                else:
                    logger.debug("No frame")
                await asyncio.sleep(1 / 30)  # Control streaming rate
            except Exception as e:
                logger.error("Error: %s", e)
                break

    return StreamingResponse(
        frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@camera_router.websocket("/ws")
async def webcam_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive text data (JSON string)
            data_str = await websocket.receive_text()
            data_json = json.loads(data_str)

            # The frame is sent as a Data URL in the format:
            # data:image/jpeg;base64,<base64-encoded-content>
            frame_data = data_json.get("frame")
            if not frame_data:
                continue  # skip if no frame found

            # Strip off the header `data:image/jpeg;base64,`
            prefix, base64_content = frame_data.split(",", 1)

            # Decode the base64 content to raw bytes
            image_bytes = base64.b64decode(base64_content)
            logger.debug("Received frame with size: %d", len(image_bytes))
            if len(image_bytes) == 0:
                logger.error("Empty frame received")
                continue

            # Optionally decode into an OpenCV image (BGR array)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            put_frame_in_queues(
                img, websocket.app.state.frame_queue, websocket.app.state.process_queue
            )

            # Do something with `img` - e.g. shape, display, process, etc.
            # This example just prints out the size:
            if img is not None:
                print("Received frame with shape:", img.shape)
            else:
                print("Failed to decode image.")

    except Exception as e:
        print("WebSocket connection closed:", e)
    finally:
        await websocket.close()
