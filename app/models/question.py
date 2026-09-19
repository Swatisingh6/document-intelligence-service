import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="unknown", nullable=False)  # mcq, multi_select, true_false, fill_blank, short_answer, descriptive, unknown
    options = Column(JSON, nullable=True)  # [{"key": "A", "text": "..."}, ...]
    answer = Column(Text, nullable=True)
    answer_confidence = Column(Float, nullable=True)
    extraction_confidence = Column(Float, default=1.0, nullable=False)
    status = Column(String(50), default="extracted", nullable=False, index=True)
    source_pages = Column(JSON, nullable=False)  # [1, 2]
    source_metadata = Column(JSON, nullable=True)  # {"ocr_used": false, ...}
    review_required = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="questions")
    images = relationship("QuestionImage", back_populates="question", cascade="all, delete-orphan")
    warnings = relationship("ExtractionWarning", back_populates="question", cascade="all, delete-orphan")


class QuestionImage(Base):
    __tablename__ = "question_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String(500), nullable=False)
    type = Column(String(50), default="image", nullable=False)

    question = relationship("Question", back_populates="images")
    page = relationship("Page", back_populates="images")
