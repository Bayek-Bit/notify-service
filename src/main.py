import logging
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import uvicorn

from src.api.v1.notifications.exceptions import (
    NotificationError,
)
from src.api.v1.notifications.router import router as api_v1_router
from src.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(NotificationError)
async def notification_error_handler(
    _request: Request, exc: NotificationError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = perf_counter()

    method = request.method
    url_path = request.base_url
    logger.info("%s %s", method, url_path)

    response = await call_next(request)
    status_code = response.status_code
    process_time = perf_counter() - start_time

    logger.info("%s %s", status_code, process_time)

    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
