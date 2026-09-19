import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import api_v1_router
from app.schemas.error import ErrorResponse, ErrorDetail

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("doc_intel_service")

# Database table creation managed via Alembic migrations (alembic upgrade head)

app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable microservice for extracting structured examination questions, options, and answers from PDF and image documents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "FILE_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR"
    }
    error_code = code_map.get(exc.status_code, "API_ERROR")
    message = str(exc.detail) if exc.detail else "An error occurred during request processing."

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": error_code, "message": message}}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}}
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Service Health Check",
    response_description="Returns system operational status"
)
def health_check():
    return {"status": "ok"}


app.include_router(api_v1_router, prefix=settings.API_V1_STR)
