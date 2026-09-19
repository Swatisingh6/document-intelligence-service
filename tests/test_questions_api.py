import io
from fastapi import status


def test_get_document_status(client, auth_headers):
    # 1. Upload a document
    file_content = b"%PDF-1.4 Mock PDF Content"
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    # 2. Check status
    status_res = client.get(f"/api/v1/documents/{doc_id}/status", headers=auth_headers)
    assert status_res.status_code == status.HTTP_200_OK
    data = status_res.json()
    assert data["document_id"] == doc_id
    assert "status" in data
    assert "progress" in data
    assert "question_count" in data


def test_list_questions_pagination(client, auth_headers):
    # Upload document
    file_content = b"%PDF-1.4 Mock PDF Content"
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    # Retrieve questions
    q_res = client.get(f"/api/v1/documents/{doc_id}/questions?page=1&page_size=10", headers=auth_headers)
    assert q_res.status_code == status.HTTP_200_OK
    data = q_res.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
