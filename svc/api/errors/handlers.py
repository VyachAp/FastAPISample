import logging
from functools import partial

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from prometheus_client import Counter
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from svc.api.errors.base import ApiError
from svc.api.models.base_model import ApiResponse, ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI, errors_counter: Counter) -> None:
    app.add_exception_handler(ApiError, partial(api_exception_handler, errors_counter=errors_counter))
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def api_exception_handler(request: Request, exc: ApiError, errors_counter: Counter) -> JSONResponse:
    logger.info(f"Api error: url={request.url}, code={exc.code}", extra={"url": request.url, "error_code": exc.code})
    errors_counter.labels("promotion-service", exc.code).inc()

    return JSONResponse(
        status_code=HTTP_200_OK,
        headers={},
        content=jsonable_encoder(ApiResponse(error=ErrorResponse(code=exc.code, data=exc.data))),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"detail": jsonable_encoder(exc.errors())},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_mapping = {HTTP_404_NOT_FOUND: "not_found", HTTP_401_UNAUTHORIZED: "unauthorized"}

    return JSONResponse(
        status_code=exc.status_code,
        headers={},
        content={
            "errors": [
                {
                    "code": status_mapping.get(exc.status_code, "code_%s" % exc.status_code),
                    "detail": str(exc.detail),
                },
            ],
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error while url={request.url}", extra={"url": request.url}, exc_info=exc)

    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        headers={},
        content={
            "errors": [
                {
                    "status": "500",
                    "code": "internal_error",
                    "detail": "Internal Server Error",
                },
            ],
        },
    )
