import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
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


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
    summary="Service Homepage & Portal"
)
def homepage():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Intelligence & Question Extraction Service</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
            --card-bg: rgba(255, 255, 255, 0.04);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-glow: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --accent-hover: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem 1rem;
        }
        .container {
            max-width: 900px;
            width: 100%;
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 3rem 2.5rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .header-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 8px #22c55e;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p.subtitle {
            font-size: 1.125rem;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 2.5rem;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }
        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.4);
            background: rgba(255, 255, 255, 0.06);
        }
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 0.75rem;
        }
        .feature-card h3 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #f1f5f9;
        }
        .feature-card p {
            font-size: 0.875rem;
            color: var(--text-muted);
            line-height: 1.5;
        }
        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
        }
        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--accent-glow);
            color: #ffffff;
            font-weight: 600;
            padding: 0.875rem 1.75rem;
            border-radius: 12px;
            text-decoration: none;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }
        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }
        .btn-secondary {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-main);
            font-weight: 500;
            padding: 0.875rem 1.5rem;
            border-radius: 12px;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }
        footer {
            margin-top: 2rem;
            font-size: 0.875rem;
            color: #64748b;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-badge">
            <span class="pulse-dot"></span> System Operational & API Live
        </div>
        <h1>Document Intelligence &<br>Question Extraction Service</h1>
        <p class="subtitle">
            An automated service that ingests PDF documents (native and scanned) and images (JPG, PNG) 
            to extract structured examination questions, multiple-choice options, answers, confidence scores, and warnings.
        </p>

        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <h3>Multi-Format Processing</h3>
                <p>Native PDF text parsing, PyMuPDF engine, and Tesseract OCR engine fallback for scanned documents and images.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">❓</div>
                <h3>Question Segmentation</h3>
                <p>Automatic detection of MCQs, short answers, options (e.g. A, B, C, D), and source page tracking.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>Answer Key Matching</h3>
                <p>Intelligent answer detection and document relationship linking with per-question confidence scoring.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚠️</div>
                <h3>Quality & Warnings</h3>
                <p>Structured extraction warnings, threshold validation, and automated flags for manual review.</p>
            </div>
        </div>

        <div class="actions">
            <a href="/docs" class="btn-primary">
                Explore API Documentation ➔
            </a>
            <a href="/health" class="btn-secondary">
                Health Check (/health)
            </a>
            <a href="/redoc" class="btn-secondary">
                ReDoc Docs
            </a>
        </div>
    </div>
    <footer>
        Document Intelligence Microservice • Production Environment
    </footer>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)


app.include_router(api_v1_router, prefix=settings.API_V1_STR)

