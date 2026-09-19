# Complete Evaluator Demonstration Script

Follow these step-by-step instructions to test and verify all key scenarios of the Document Intelligence & Question Extraction Service.

---

## Step 1: Start Services with Docker Compose
```bash
docker compose up --build -d
```
Verify all containers are running cleanly:
```bash
docker compose ps
```
Or view container logs:
```bash
docker compose logs -f api
```

---

## Step 2: Open Swagger Documentation UI
Open your browser and navigate to:
```
http://localhost:8000/docs
```
You will see interactive Swagger documentation with full API schemas, request/response models, and trial capabilities.

---

## Scenario 1: User Registration & JWT Authentication
1. Execute `POST /api/v1/auth/register` with payload:
   ```json
   {
     "email": "evaluator@company.com",
     "password": "Password123!"
   }
   ```
2. Execute `POST /api/v1/auth/login` to obtain the JWT token.
3. Click **Authorize** at the top right of Swagger UI and enter `Bearer <YOUR_ACCESS_TOKEN>`.

---

## Scenario 2: Upload Digital PDF Document
1. Execute `POST /api/v1/documents/upload` uploading `samples/clean_digital.pdf`.
2. Copy the returned `document_id`.

---

## Scenario 3: Check Asynchronous Processing Status
1. Execute `GET /api/v1/documents/{document_id}/status`.
2. Observe `status`: `"completed"`, `progress`: `100.0`, `question_count`: `2`.

---

## Scenario 4: Retrieve Structured Questions & Options
1. Execute `GET /api/v1/documents/{document_id}/questions`.
2. Observe structured question json output containing `question_number`, `question_text`, `options` array (`A`, `B`, `C`, `D`), `answer`, and explainable `confidence` scores.

---

## Scenario 5: Multi-Page Question Spanning Verification
1. Upload `samples/multipage_question.pdf`.
2. Retrieve its questions via `GET /api/v1/documents/{doc_id}/questions`.
3. Observe **Question 2**:
   - `source_pages`: `[1, 2]`
   - `options`: contains all 4 options `A`, `B`, `C`, `D` merged across page boundary.

---

## Scenario 6: Image Question Paper Upload & OCR Fallback
1. Upload `samples/scanned_exam.png`.
2. Check status via `GET /api/v1/documents/{doc_id}/status`.
3. Retrieve questions to verify OCR text extraction and option parsing.

---

## Scenario 7: Separate Answer-Key Document Relationship Link
1. Upload question paper document `samples/clean_digital.pdf` (note ID).
2. Upload standalone answer key document `samples/answer_key_separate.pdf` (note ID).
3. Execute `POST /api/v1/documents/{question_doc_id}/relationships` with body:
   ```json
   {
     "related_document_id": "<ANSWER_KEY_DOC_ID>",
     "relationship_type": "answer_key"
   }
   ```
4. Query answers via `GET /api/v1/documents/{question_doc_id}/answers` to observe answer association.

---

## Scenario 8: Ambiguous Document & Review Warning Verification
1. Upload `samples/ambiguous_scan.png`.
2. Execute `GET /api/v1/documents/{doc_id}/warnings`.
3. Observe typed warnings such as `MISSING_QUESTION_NUMBER` and `ANSWER_UNMATCHED`.
4. Execute `GET /api/v1/documents/{doc_id}/questions?review_required=true` to see flagged questions.

---

## Scenario 9: File Validation & Unsupported File Rejection
1. Upload `samples/invalid_file.exe`.
2. Observe HTTP 400 response:
   ```json
   {
     "error": {
       "code": "BAD_REQUEST",
       "message": "Unsupported file extension '.exe'..."
     }
   }
   ```
