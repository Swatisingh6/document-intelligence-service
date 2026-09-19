import io
from fastapi import status


def test_upload_pdf_success(client, auth_headers):
    file_content = b"%PDF-1.4 Mock PDF Content Header"
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_200_OK]
    data = response.json()
    assert "document_id" in data
    assert data["status"] in ["queued", "completed", "completed_with_warnings"]


def test_upload_invalid_extension(client, auth_headers):
    file_content = b"Binary executable payload"
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("script.exe", io.BytesIO(file_content), "application/x-msdownload")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file extension" in response.json()["error"]["message"]


def test_upload_unauthorized(client):
    file_content = b"%PDF-1.4 Mock PDF Content"
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
