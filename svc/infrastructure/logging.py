import logging
import logging.config
from pathlib import Path
from typing import Any

import yaml

from svc.infrastructure.traces import trace_id_context_var
from svc.settings import LoggingProfileEnum

logger = logging.getLogger(__name__)
CONFIGURATION_DIRECTORY = "logging_profiles"


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


def configure_logging(logging_profile: LoggingProfileEnum) -> None:
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    path = Path(CONFIGURATION_DIRECTORY) / f"{logging_profile.value}.yaml"
    logger.info(f"Using {path} logging configuration")

    if path.exists():
        with path.open("rt") as file:
            config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
    else:
        logger.info(f"No {path} logging configuration, use basic logging")
        logging.basicConfig(level=logging.DEBUG)
    logging.setLogRecordFactory(RequestedLogRecord)


class RequestedLogRecord(logging.LogRecord):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.trace_id = trace_id_context_var.get()
        super().__init__(*args, **kwargs)
