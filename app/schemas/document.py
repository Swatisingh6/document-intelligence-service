from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    progress: float = Field(..., description="Progress percentage (0.0 to 100.0)")
    current_stage: str
    page_count: int
    processed_pages: int
    warning_count: int
    question_count: int
    error: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    owner_id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    document_type: str
    status: str
    page_count: int
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRelationshipCreate(BaseModel):
    related_document_id: str
    relationship_type: str = Field(..., description="e.g. answer_key, supplement, continuation")


class DocumentRelationshipResponse(BaseModel):
    id: str
    source_document_id: str
    related_document_id: str
    relationship_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
