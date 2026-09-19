import io
from fastapi import status


def test_create_and_delete_document_relationship(client, auth_headers):
    # Upload source doc
    res1 = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("paper.pdf", io.BytesIO(b"%PDF-1.4 Question Paper"), "application/pdf")}
    )
    doc1_id = res1.json()["document_id"]

    # Upload target doc
    res2 = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("key.pdf", io.BytesIO(b"%PDF-1.4 Answer Key"), "application/pdf")}
    )
    doc2_id = res2.json()["document_id"]

    # Create relationship
    rel_res = client.post(
        f"/api/v1/documents/{doc1_id}/relationships",
        headers=auth_headers,
        json={"related_document_id": doc2_id, "relationship_type": "answer_key"}
    )
    assert rel_res.status_code == status.HTTP_201_CREATED
    rel_data = rel_res.json()
    rel_id = rel_data["id"]
    assert rel_data["source_document_id"] == doc1_id
    assert rel_data["related_document_id"] == doc2_id
    assert rel_data["relationship_type"] == "answer_key"

    # List relationships
    list_res = client.get(f"/api/v1/documents/{doc1_id}/relationships", headers=auth_headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # Delete relationship
    del_res = client.delete(f"/api/v1/documents/{doc1_id}/relationships/{rel_id}", headers=auth_headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
