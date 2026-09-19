import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.question import Question
from app.models.warning import ExtractionWarning
from app.schemas.question import QuestionResponse, PaginatedQuestionsResponse, OptionSchema
from app.schemas.warning import ExtractionWarningResponse
from app.security.auth import get_current_user

router = APIRouter(tags=["Questions"])


def build_question_schema(q: Question, db: Session) -> QuestionResponse:
    """Helper to convert Question ORM object to QuestionResponse schema."""
    warnings_orm = db.query(ExtractionWarning).filter(ExtractionWarning.question_id == q.id).all()
    warnings_schema = [
        ExtractionWarningResponse(
            id=w.id,
            document_id=w.document_id,
            question_id=w.question_id,
            page_number=w.page_number,
            warning_type=w.warning_type,
            message=w.message,
            severity=w.severity,
            confidence=w.confidence,
            created_at=w.created_at
        )
        for w in warnings_orm
    ]

    options_schema = None
    if q.options and isinstance(q.options, list):
        options_schema = [OptionSchema(key=opt.get("key", ""), text=opt.get("text", "")) for opt in q.options]

    return QuestionResponse(
        id=q.id,
        question_number=q.question_number,
        question_text=q.question_text,
        question_type=q.question_type,
        options=options_schema,
        answer=q.answer,
        answer_confidence=q.answer_confidence,
        source_document_id=q.document_id,
        source_pages=q.source_pages or [1],
        confidence=q.extraction_confidence,
        review_required=q.review_required,
        warnings=warnings_schema,
        created_at=q.created_at
    )


@router.get(
    "/documents/{document_id}/questions",
    response_model=PaginatedQuestionsResponse,
    summary="List extracted questions for document with filtering & pagination"
)
def list_document_questions(
    document_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    review_required: Optional[bool] = Query(None, description="Filter by review_required status"),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence filter"),
    question_type: Optional[str] = Query(None, description="Filter by question_type (mcq, true_false, etc.)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    query = db.query(Question).filter(Question.document_id == document_id)

    if review_required is not None:
        query = query.filter(Question.review_required == review_required)

    if confidence_min is not None:
        query = query.filter(Question.extraction_confidence >= confidence_min)

    if question_type:
        query = query.filter(Question.question_type == question_type)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    questions_orm = query.order_by(Question.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [build_question_schema(q, db) for q in questions_orm]

    return PaginatedQuestionsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Get single question details"
)
def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    doc = db.query(Document).filter(Document.id == q.document_id).first()
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    return build_question_schema(q, db)
