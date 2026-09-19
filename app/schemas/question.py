from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.warning import ExtractionWarningResponse


class OptionSchema(BaseModel):
    key: str = Field(..., json_schema_extra={"example": "A"})
    text: str = Field(..., json_schema_extra={"example": "Option description text"})


class QuestionResponse(BaseModel):
    id: str
    question_number: str
    question_text: str
    question_type: str  # mcq, multi_select, true_false, fill_blank, short_answer, descriptive, unknown
    options: Optional[List[OptionSchema]] = None
    answer: Optional[str] = None
    answer_confidence: Optional[float] = None
    source_document_id: str
    source_pages: List[int]
    confidence: float
    review_required: bool
    warnings: List[ExtractionWarningResponse] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnswerDetailResponse(BaseModel):
    question_id: str
    question_number: str
    answer: Optional[str]
    answer_confidence: Optional[float]
    review_required: bool


class PaginatedQuestionsResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
