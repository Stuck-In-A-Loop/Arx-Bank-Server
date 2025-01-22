import asyncio
from .logger import logger
from .global_settings import settings
from .queues import frame_queue
from .endpoint_logging_filter import EndpointLoggingFilter
from .types import DetectionStatus


def get_or_create_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:  # No event loop exists in the current context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
