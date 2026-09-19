import os
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentRelationship
from app.models.page import Page
from app.models.question import Question
from app.models.warning import ExtractionWarning
from app.models.job import ProcessingJob
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentResponse,
    DocumentRelationshipCreate,
    DocumentRelationshipResponse,
)
from app.schemas.warning import ExtractionWarningResponse
from app.schemas.question import AnswerDetailResponse
from app.security.auth import get_current_user
from app.storage.storage_service import storage_service
from app.workers.tasks import process_document_task, run_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload PDF or image document for processing",
    description="Accepts PDF/JPG/JPEG/PNG documents up to configured size limit, stores securely, and enqueues async processing."
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    # 1. Extension validation
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. MIME type validation
    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_MIME_TYPES:
        # Graceful check for standard browser MIME variations
        if not (ext in [".jpg", ".jpeg"] and "image" in content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type '{content_type}'. Allowed MIME types: PDF, JPG, JPEG, PNG."
            )

    # 3. Read file content & check size limit
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 4. Save file via Storage Service
    try:
        storage_key = storage_service.save_file(content, filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file securely: {str(e)}"
        )

    # 5. Create Document record
    doc = Document(
        owner_id=current_user.id,
        filename=storage_key,
        original_filename=filename,
        content_type=content_type,
        file_size=file_size,
        storage_path=storage_key,
        document_type="pdf" if ext == ".pdf" else "image",
        status="queued"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Create ProcessingJob record
    task_id = str(uuid.uuid4())
    job = ProcessingJob(
        document_id=doc.id,
        celery_task_id=task_id,
        status="queued",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()

    # 7. Enqueue Celery Task with fallback to sync run for test environments
    try:
        if settings.APP_ENV in ["testing", "development"] and not os.getenv("FORCE_CELERY"):
            run_pipeline(doc.id, db)
        else:
            try:
                process_document_task.apply_async(args=[doc.id], connect_timeout=1)
            except Exception:
                run_pipeline(doc.id, db)
    except Exception:
        run_pipeline(doc.id, db)

    return DocumentUploadResponse(
        document_id=doc.id,
        status="queued",
        message="Document uploaded successfully and queued for asynchronous processing"
    )


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List all documents owned by user"
)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).filter(Document.owner_id == current_user.id).order_by(Document.created_at.desc()).all()
    return docs


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details"
)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get processing status and progress"
)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    page_count = db.query(Page).filter(Page.document_id == document_id).count()
    processed_pages = page_count  # All stored pages are processed
    warning_count = db.query(ExtractionWarning).filter(ExtractionWarning.document_id == document_id).count()
    question_count = db.query(Question).filter(Question.document_id == document_id).count()

    # Stage progress mapping
    progress_map = {
        "queued": 0.0,
        "validating": 15.0,
        "extracting_text": 30.0,
        "ocr_processing": 50.0,
        "extracting_questions": 70.0,
        "extracting_answers": 85.0,
        "completed": 100.0,
        "completed_with_warnings": 100.0,
        "failed": 0.0
    }
    progress = progress_map.get(doc.status, 50.0)

    return DocumentStatusResponse(
        document_id=doc.id,
        status=doc.status,
        progress=progress,
        current_stage=doc.status,
        page_count=doc.page_count or page_count,
        processed_pages=processed_pages,
        warning_count=warning_count,
        question_count=question_count,
        error=doc.error_message
    )


@router.get(
    "/{document_id}/answers",
    response_model=List[AnswerDetailResponse],
    summary="Get extracted answers for document questions"
)
def get_document_answers(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    questions = db.query(Question).filter(Question.document_id == document_id).all()
    results = [
        AnswerDetailResponse(
            question_id=q.id,
            question_number=q.question_number,
            answer=q.answer,
            answer_confidence=q.answer_confidence,
            review_required=q.review_required
        )
        for q in questions
    ]
    return results


@router.get(
    "/{document_id}/warnings",
    response_model=List[ExtractionWarningResponse],
    summary="Get extraction warnings for document"
)
def get_document_warnings(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    warnings = db.query(ExtractionWarning).filter(ExtractionWarning.document_id == document_id).all()
    return warnings


@router.post(
    "/{document_id}/relationships",
    response_model=DocumentRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document relationship (e.g. answer_key link)"
)
def create_relationship(
    document_id: str,
    rel_in: DocumentRelationshipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source_doc = db.query(Document).filter(Document.id == document_id).first()
    if not source_doc or source_doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source document not found")

    target_doc = db.query(Document).filter(Document.id == rel_in.related_document_id).first()
    if not target_doc or target_doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related document not found")

    rel = DocumentRelationship(
        source_document_id=source_doc.id,
        related_document_id=target_doc.id,
        relationship_type=rel_in.relationship_type
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


@router.get(
    "/{document_id}/relationships",
    response_model=List[DocumentRelationshipResponse],
    summary="List document relationships"
)
def get_relationships(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source_doc = db.query(Document).filter(Document.id == document_id).first()
    if not source_doc or source_doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    rels = db.query(DocumentRelationship).filter(DocumentRelationship.source_document_id == document_id).all()
    return rels


@router.delete(
    "/{document_id}/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document relationship"
)
def delete_relationship(
    document_id: str,
    relationship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rel = db.query(DocumentRelationship).filter(
        DocumentRelationship.id == relationship_id,
        DocumentRelationship.source_document_id == document_id
    ).first()

    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")

    db.delete(rel)
    db.commit()
    return None
