from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import uvicorn

from src.api.v1.notifications.exceptions import (
    NotificationError,
)
from src.api.v1.notifications.logging_service import logger
from src.api.v1.notifications.router import router as api_v1_router
from src.config import settings

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Инициализация Sentry
sentry_sdk.init(
    dsn="https://ac74db3ec166c2a09b39980d7910f5b2@o4511156331020288.ingest.us.sentry.io/4511156333248512",
    integrations=[FastApiIntegration()],
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


# вставка через %s и **kwargs, который написан в классе LoggerService. Не будет ли конфликта? И почему?
@app.exception_handler(NotificationError)
async def notification_error_handler(
    _request: Request, exc: NotificationError
) -> JSONResponse:
    logger.error(
        "Ошибка NotificationError",
        status_code=exc.status_code,
        detail=exc.detail,
        query_params=_request.query_params,
        exc_info=True,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = perf_counter()

    method = request.method
    url_path = request.url.path
    logger.info("HTTP Запрос %s %s", method=method, url_path=url_path)

    response = await call_next(request)
    status_code = response.status_code
    process_time = perf_counter() - start_time

    logger.info(
        "Ответ на запрос получен %s %s",
        status_code=status_code,
        process_time=process_time,
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
