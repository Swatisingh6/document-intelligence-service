# Document Intelligence & Question Extraction Service

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.3.6-37814A.svg?style=flat-square&logo=celery)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat-square&logo=docker)](https://www.docker.com/)

A scalable enterprise microservice that accepts PDF examination documents and images (scans, JPG, PNG), performs text extraction and local OCR preprocessing, segments questions and options (including questions spanning multiple pages), maps answer keys, and calculates explainable confidence scores for review.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Folder Structure](#5-project-folder-structure)
6. [Prerequisites](#6-prerequisites)
7. [Docker Setup & Deployment](#7-docker-setup--deployment)
8. [Local Development Setup](#8-local-development-setup)
9. [Environment Variables](#9-environment-variables)
10. [Database Migrations](#10-database-migrations)
11. [Starting the API Service](#11-starting-the-api-service)
12. [Starting the Celery Worker](#12-starting-the-celery-worker)
13. [API Documentation & Examples](#13-api-documentation--examples)
14. [Swagger & OpenAPI Specs](#14-swagger--openapi-specs)
15. [Postman Collection Instructions](#15-postman-collection-instructions)
16. [Sample Test Documents](#16-sample-test-documents)
17. [Processing Pipeline Stages](#17-processing-pipeline-stages)
18. [OCR Implementation Approach](#18-ocr-implementation-approach)
19. [Optional AI / LLM Approach](#19-optional-ai--llm-approach)
20. [Explainable Confidence Mechanism](#20-explainable-confidence-mechanism)
21. [Security Implementation](#21-security-implementation)
22. [Scalability & Concurrency](#22-scalability--concurrency)
23. [Automated Testing](#23-automated-testing)
24. [Known Limitations](#24-known-limitations)
25. [Design Trade-offs](#25-design-trade-offs)
26. [Future Improvements](#26-future-improvements)

---

## 1. Project Overview
Assessment platforms require ingestion of examination papers, question banks, and answer keys in various document formats (digital PDFs, scanned papers, images). Manual keying is slow and error-prone. This service automates text/OCR extraction, question boundary detection, option structuring, multi-page continuation merging, answer key association, and confidence scoring via a modular REST API.

---

## 2. Key Features
- **Multi-Format Support**: Handles digital PDFs, scanned PDFs, JPG/JPEG, and PNG.
- **Robust Question Boundary Detection**: Detects diverse numbering formats (`1.`, `2)`, `Q1.`, `Question 1:`, `(1)`).
- **Multi-Page Question Continuation**: Merges questions and options that span page boundaries into single question structures with `source_pages: [1, 2]`.
- **Option Extraction**: Parses multi-line and inline options (`A.`, `B)`, `(a)`, `1)`) into structured JSON array objects.
- **Answer Key Association**: Automatically extracts answer keys from same document or linked `answer_key` documents.
- **Explainable Confidence Scoring**: Calculates 0.0 - 1.0 signal-weighted confidence score based on OCR, header clarity, option count, and answer matching.
- **Review & Warning Engine**: Generates typed warnings (`OCR_LOW_CONFIDENCE`, `ANSWER_UNMATCHED`, `MISSING_QUESTION_NUMBER`, etc.) and flags `review_required = True`.
- **Pluggable Architecture**: Storage abstraction (`LocalStorageProvider`), OCR engine (`TesseractOcrProvider`), and optional LLM service (`GeminiLLMProvider`).

---

## 3. System Architecture
```
Client Platform  -->  FastAPI Application  -->  Redis Queue  -->  Celery Workers
                           |                                           |
                    PostgreSQL Database                        PyMuPDF + OpenCV + OCR
```
Detailed architecture diagrams and sequence flows are documented in [docs/ARCHITECTURE.md](file:///c:/Users/swati/Desktop/pnbc/docs/ARCHITECTURE.md).

---

## 4. Technology Stack
- **API Framework**: FastAPI 0.110+, Uvicorn
- **Database & ORM**: PostgreSQL 16, SQLAlchemy 2.0+, Alembic
- **Async Queue**: Redis 7, Celery 5.3+
- **Document Processing**: PyMuPDF (`fitz`), Pillow, OpenCV (`opencv-python-headless`), PyTesseract
- **Authentication**: JWT (PyJWT), Passlib (Bcrypt)
- **Validation**: Pydantic v2, Pydantic Settings
- **Testing & Tooling**: Pytest, HTTPX, ReportLab

---

## 5. Project Folder Structure
```
document-intelligence-service/
├── app/
│   ├── api/v1/          # FastAPI routers (auth, documents, questions)
│   ├── core/            # Config, database session, celery app
│   ├── extraction/      # Text extractor, question segmenter, option parser, answer detector
│   ├── models/          # SQLAlchemy 2.0 ORM models
│   ├── ocr/             # OCR engine abstraction & Tesseract implementation
│   ├── schemas/         # Pydantic v2 validation models
│   ├── security/        # JWT auth & password hashing
│   ├── services/        # LLM service abstraction
│   ├── storage/         # StorageProvider abstraction & LocalStorageProvider
│   ├── workers/         # Celery tasks
│   └── main.py          # FastAPI application entrypoint
├── alembic/             # Database migration scripts
├── docs/                # Architecture, design decisions, demo scripts, API curl examples
├── postman/             # Postman Collection JSON
├── samples/             # Sample test documents generator & generated files
├── scripts/             # Utility scripts
├── tests/               # Automated Pytest test suite
├── Dockerfile           # Multi-stage container definition
├── docker-compose.yml   # API, Worker, PostgreSQL, Redis, Flower services
├── requirements.txt     # Dependency manifest
└── README.md
```

---

## 6. Prerequisites
- **Docker & Docker Compose** (Recommended) OR
- **Python 3.10+**, **PostgreSQL**, **Redis**, and **Tesseract OCR system binary** installed locally.

---

## 7. Docker Setup & Deployment
Run the complete stack (API, Celery worker, PostgreSQL, Redis, Flower) with a single command:
```bash
docker compose up --build
```
The API will be available at `http://localhost:8000`. Flower task monitor will be available at `http://localhost:5555`.

---

## 8. Local Development Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

---

## 9. Environment Variables
Configurations are loaded via Pydantic settings from `.env`:
```env
APP_ENV=development
DEBUG=True
SECRET_KEY=super-secret-jwt-signing-key
DATABASE_URL=sqlite:///./doc_intel.db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE_MB=20
TESSERACT_CMD=tesseract
LLM_PROVIDER=none
```

---

## 10. Database Migrations
Apply database migrations using Alembic:
```bash
alembic upgrade head
```

---

## 11. Starting the API Service
Run Uvicorn dev server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 12. Starting the Celery Worker
Run Celery worker process:
```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

---

## 13. API Documentation & Examples
Ready-to-use cURL commands for all endpoints are available in [docs/API_EXAMPLES.md](file:///c:/Users/swati/Desktop/pnbc/docs/API_EXAMPLES.md).

---

## 14. Swagger & OpenAPI Specs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 15. Postman Collection Instructions
Import `postman/Document-Intelligence-Service.postman_collection.json` into Postman. Execute requests in order:
1. Register
2. Login (auto-populates `{{token}}`)
3. Upload PDF / Image
4. Check Status
5. List Questions & View Details

---

## 16. Sample Test Documents
Generate synthetic sample files:
```bash
python scripts/generate_samples.py
```
Generated samples in `samples/`:
1. `clean_digital.pdf`: Clean digital examination PDF.
2. `scanned_exam.png`: Image-based question paper.
3. `multipage_question.pdf`: Question 2 spanning Page 1 and Page 2.
4. `answer_key_separate.pdf`: Standalone answer key.
5. `ambiguous_scan.png`: Low contrast unnumbered question paper.
6. `invalid_file.exe`: Binary file for validation rejection.

---

## 17. Processing Pipeline Stages
1. **Validation**: Check content type, extension, size.
2. **Text Extraction**: PyMuPDF vector text extraction.
3. **OCR Fallback**: OpenCV deskewing + Tesseract OCR for scans.
4. **Question Segmentation**: Header regex matching & cross-page continuation merging.
5. **Option Parsing**: Extract options $A/B/C/D$ in multi-line/inline formats.
6. **Answer Detection**: Match answers from text headers or linked `answer_key` documents.
7. **Confidence Scoring**: Compute explainable signal-weighted score ($0.0 - 1.0$).

---

## 18. OCR Implementation Approach
Utilizes `TesseractOcrProvider` backed by OpenCV image processing:
- Converts page images to grayscale and applies `fastNlMeansDenoising`.
- Binarizes using Otsu thresholding.
- Calculates minimum bounding rect angle and rotates image to deskew prior to Tesseract OCR.
- Returns extracted text and average character confidence score.

---

## 19. Optional AI / LLM Approach
External AI is wrapped behind the `LLMProvider` interface (`GeminiLLMProvider`). Set `LLM_PROVIDER=gemini` and `LLM_API_KEY`. If set to `LLM_PROVIDER=none` or credentials are missing, the system operates seamlessly using deterministic parsing without error.

---

## 20. Explainable Confidence Mechanism
Overall confidence score is computed as:
$$\text{Score} = 0.25 S_{\text{ocr}} + 0.30 S_{\text{boundary}} + 0.25 S_{\text{options}} + 0.20 S_{\text{answer}}$$
If $\text{Score} < 0.60$ or an answer is missing, `review_required` is set to `True` and typed `ExtractionWarning` entries are created.

---

## 21. Security Implementation
- **JWT Authentication**: Bearer token headers verified on protected routes.
- **Path Traversal Protection**: Storage keys resolved securely against base path.
- **Upload Validation**: Extension, MIME, and max file size checks.
- **Password Security**: Passlib Bcrypt hashing.

---

## 22. Scalability & Concurrency
- Stateless FastAPI instances scale horizontally.
- Redis queues distribute Celery extraction tasks across worker nodes.
- File contents stored outside PostgreSQL in file storage.

---

## 23. Automated Testing
Run the complete Pytest suite:
```bash
pytest -v
```

---

## 24. Known Limitations
- Complex nested table extraction is represented as structured plain text.
- Handwriting OCR quality depends on Tesseract model training.

---

## 25. Design Trade-offs
Detailed trade-off analysis is documented in [docs/DESIGN_DECISIONS.md](file:///c:/Users/swati/Desktop/pnbc/docs/DESIGN_DECISIONS.md).

---

## 26. Future Improvements
- Add support for Amazon S3 / MinIO cloud storage drivers.
- Implement specialized LaTeX math expression extraction.
- Provide real-time WebSockets progress updates for large document uploads.
