# API Curl Examples

## 1. Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "securepassword123"
  }'
```

## 2. User Login & Obtain Bearer Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "securepassword123"
  }'
```

## 3. Upload Digital PDF Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -F "file=@samples/clean_digital.pdf"
```

## 4. Check Document Processing Status
```bash
curl -X GET "http://localhost:8000/api/v1/documents/<DOCUMENT_ID>/status" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 5. Retrieve Extracted Questions (Filtered & Paginated)
```bash
curl -X GET "http://localhost:8000/api/v1/documents/<DOCUMENT_ID>/questions?page=1&page_size=20&review_required=false" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 6. Retrieve Single Question Details
```bash
curl -X GET "http://localhost:8000/api/v1/questions/<QUESTION_ID>" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 7. Retrieve Document Answers
```bash
curl -X GET "http://localhost:8000/api/v1/documents/<DOCUMENT_ID>/answers" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 8. Retrieve Extraction Warnings
```bash
curl -X GET "http://localhost:8000/api/v1/documents/<DOCUMENT_ID>/warnings" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 9. Create Document Relationship (Answer-Key Link)
```bash
curl -X POST "http://localhost:8000/api/v1/documents/<SOURCE_DOC_ID>/relationships" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "related_document_id": "<ANSWER_KEY_DOC_ID>",
    "relationship_type": "answer_key"
  }'
```
