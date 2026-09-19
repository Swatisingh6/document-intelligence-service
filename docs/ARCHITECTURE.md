# System Architecture - Document Intelligence Service

## Architecture Overview

The Document Intelligence & Question Extraction Service is built around an asynchronous, event-driven processing pipeline designed to ingest, process, and extract structured examination content from PDFs and images reliably.

```mermaid
flowchart TD
    Client[Client / Assessment Platform]
    
    subgraph API Layer
        FastAPI[FastAPI Application]
        Auth[JWT Authentication & Security]
        Upload[Upload Endpoint]
    end

    subgraph Storage & Queue
        Redis[(Redis Message Broker)]
        Postgres[(PostgreSQL Database)]
        LocalStorage[Local File Storage]
    end

    subgraph Async Processing
        Worker[Celery Worker Cluster]
        PDFEngine[PyMuPDF Text Engine]
        OCREngine[OpenCV + Tesseract OCR]
        Segmenter[Question & Option Segmenter]
        AnswerDetector[Answer Key & Document Relator]
        ConfidenceEngine[Explainable Confidence Engine]
        LLM[Optional LLM Refinement Layer]
    end

    Client -->|1. HTTP Request| FastAPI
    FastAPI --> Auth
    Upload -->|2. Save File| LocalStorage
    Upload -->|3. Persist Metadata| Postgres
    Upload -->|4. Enqueue Task| Redis
    Redis -->|5. Consume Task| Worker
    
    Worker -->|6. Extract Text| PDFEngine
    PDFEngine -->|Fallback if Scan| OCREngine
    Worker -->|7. Parse Questions| Segmenter
    Worker -->|8. Map Answers| AnswerDetector
    Worker -->|9. Score Signals| ConfidenceEngine
    ConfidenceEngine -.->|Optional Refine| LLM
    Worker -->|10. Save Results & Warnings| Postgres
```

---

## Processing Pipeline Stages

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant FastAPI
    participant Redis
    participant Worker
    participant DB as PostgreSQL
    participant Storage

    Client->>FastAPI: POST /api/v1/documents/upload (PDF/Image)
    FastAPI->>Storage: Save file securely (Path Traversal Protected)
    FastAPI->>DB: Create Document (status: queued) & Job record
    FastAPI->>Redis: Enqueue process_document_task(document_id)
    FastAPI-->>Client: Return HTTP 202 Accepted (document_id)

    Redis->>Worker: Dispatch task
    Worker->>DB: Update status (validating -> extracting_text)
    
    alt Digital PDF
        Worker->>Worker: Extract text via PyMuPDF (fitz)
    else Scanned PDF / Image
        Worker->>Worker: Render at 300 DPI -> OpenCV Deskew & Binarization -> Tesseract OCR
    end

    Worker->>DB: Create Page records (ocr_used flag)
    Worker->>Worker: Question Segmentation (Boundary regex & multi-page continuation)
    Worker->>Worker: Option Parsing (Multi-line & Inline formats)
    Worker->>Worker: Answer Key Detection & Association (Internal + Related Docs)
    Worker->>Worker: Compute Explainable Confidence Signals (OCR, Boundary, Options, Answer)
    Worker->>DB: Store Questions, Options JSONB, and ExtractionWarnings
    Worker->>DB: Update Document status (completed / completed_with_warnings)
```

---

## Core Components

### 1. API Layer (`app/api/`)
- Built with **FastAPI** for high performance, automatic OpenAPI documentation, and native Pydantic v2 data validation.
- Enforces JWT Bearer authentication for strict tenant isolation.

### 2. File Storage Abstraction (`app/storage/`)
- Implements `StorageProvider` interface with `LocalStorageProvider` concrete class.
- Prevents path traversal security vulnerabilities by enforcing canonical directory resolution.

### 3. Extraction Engine (`app/extraction/`)
- **PyMuPDF (`fitz`)**: Extracts vector text from digital PDFs.
- **OpenCV + Tesseract (`app/ocr/`)**: Automatically deskews, binarizes, and OCRs pages when native text density is low (< 50 chars/page).
- **Question Segmenter**: Uses pattern matchers to detect question headers (`1.`, `Q1.`, `Question 1:`, `(1)`), handles missing question numbers using generated IDs, and merges questions spanning multiple pages.
- **Option Extractor**: Parses options `A.`, `B)`, `(a)`, `1)` in both multi-line and inline formats.
- **Answer Detector**: Extracts key-value mappings (`1-A`, `2. C`) from text or linked `answer_key` documents.

### 4. Explainable Confidence Scoring (`app/extraction/confidence_calculator.py`)
Calculates a signal-weighted score (0.0 to 1.0):
$$\text{Score} = 0.25 \times S_{\text{ocr}} + 0.30 \times S_{\text{boundary}} + 0.25 \times S_{\text{options}} + 0.20 \times S_{\text{answer}}$$

Items with score $< 0.60$ or missing required answers set `review_required = True` and emit typed `ExtractionWarning` entries.

---

## Horizontal Scalability Strategy

- **Stateless API Instances**: FastAPI app instances can be scaled horizontally behind an NGINX / Cloud Load Balancer.
- **Celery Worker Pool**: Celery workers scale independently across worker nodes consuming from Redis queues.
- **Database Connection Pooling**: SQLAlchemy manages connection pooling to PostgreSQL.
