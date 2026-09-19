# Design Decisions & Technical Trade-offs

## 1. Deterministic-First Processing vs. LLM Dependency
**Decision**: Primary text extraction, question segmentation, option parsing, and answer association are built using deterministic regex patterns, PyMuPDF, OpenCV, and local OCR.
**Rationale**:
- **Cost Efficiency & Speed**: Deterministic parsing completes in milliseconds without external API costs or rate limits.
- **Reproducibility**: Produces identical output for identical documents, facilitating automated unit testing.
- **Graceful Fallback**: External AI providers (Gemini / OpenAI) are wrapped behind an `LLMProvider` interface and optional refinement step. If credentials are absent (`LLM_PROVIDER=none`), the core pipeline operates at 100% functionality.

---

## 2. Multi-Page Question Continuation Logic
**Decision**: When segmenting questions, the system checks across page boundaries. If page $N$ ends with a question (e.g. options A and B) and page $N+1$ starts without a new question header (e.g. options C and D), content is appended to the previous question, setting `source_pages: [N, N+1]`.
**Rationale**: Examination question papers frequently split multi-choice options across page breaks. Creating separate artificial questions at page boundaries corrupts question structure and assessment platform imports.

---

## 3. Explainable Confidence Scoring vs. Silent Guessing
**Decision**: Scores questions between 0.0 and 1.0 using explicit signal weights (OCR quality, boundary header clarity, option completeness, answer mapping). If score $< 0.60$, the system flags `review_required = True` and generates typed `ExtractionWarning` records.
**Rationale**: In assessment platforms, silently guessing incorrect options or answers introduces exam invalidity. Exposing transparent confidence scores and warnings allows human reviewers to quickly verify low-confidence items.

---

## 4. Asynchronous Task Processing with Celery & Redis
**Decision**: Document uploads return HTTP 202 Accepted immediately with a `document_id` and status `queued`. Extraction runs asynchronously in Celery workers.
**Rationale**: OCR and multi-page PDF processing can take several seconds. Synchronous handling in HTTP request handlers would cause timeouts under high load.

---

## 5. Storage Abstraction with Path Traversal Protection
**Decision**: Files are stored using `LocalStorageProvider` generating UUID filenames. Resolving file paths enforces strict checking against the base storage path.
**Rationale**: Prevents malicious path traversal attacks (e.g. filenames containing `../../etc/passwd`). The abstraction permits seamlessly swapping to S3 or MinIO without modifying business logic.
