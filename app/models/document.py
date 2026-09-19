import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    document_type = Column(String(50), default="unknown", nullable=False)
    status = Column(String(50), default="queued", nullable=False, index=True)
    page_count = Column(Integer, default=0, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
    warnings = relationship("ExtractionWarning", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
    
    # Relationships where this doc is the source
    source_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.source_document_id",
        back_populates="source_document",
        cascade="all, delete-orphan"
    )
    # Relationships where this doc is the related doc
    target_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.related_document_id",
        back_populates="related_document",
        cascade="all, delete-orphan"
    )


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    related_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False)  # 'answer_key', 'supplement', 'continuation'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_document = relationship("Document", foreign_keys=[source_document_id], back_populates="source_relationships")
    related_document = relationship("Document", foreign_keys=[related_document_id], back_populates="target_relationships")
