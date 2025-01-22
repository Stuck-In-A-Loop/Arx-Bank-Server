"""Healthcheck endpoints."""

import logging

from fastapi import APIRouter, Response, status

from arx_bank_server.setup import EndpointLoggingFilter

router = APIRouter(tags=["healthcheck"])


def init_healthcheck():
    """Initialize healthcheck endpoints."""
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(EndpointLoggingFilter(path="/healthcheck"))


@router.get("/healthcheck")
async def healthcheck():
    """Healthcheck endpoint."""
    return {"status": "ok"}


@router.head("/healthcheck", status_code=status.HTTP_204_NO_CONTENT)
async def get_health_head(response: Response):
    """Healthcheck endpoint."""
    response.headers["X-Status"] = "ok"
