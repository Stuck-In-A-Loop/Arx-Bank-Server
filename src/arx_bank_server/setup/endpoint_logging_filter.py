"""Filter out logs from a specific endpoint."""

import logging
import typing as t


class EndpointLoggingFilter(logging.Filter):
    """Filter out logs from a specific endpoint."""

    def __init__(
        self,
        path: str,
        *args: t.Any,
        **kwargs: t.Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1
