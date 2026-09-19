from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtractionWarningResponse(BaseModel):
    id: str
    document_id: str
    question_id: Optional[str] = None
    page_number: Optional[int] = None
    warning_type: str
    message: str
    severity: str
    confidence: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
