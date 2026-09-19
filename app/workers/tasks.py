import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, DocumentRelationship
from app.models.page import Page
from app.models.question import Question, QuestionImage
from app.models.warning import ExtractionWarning
from app.models.job import ProcessingJob

from app.extraction.pdf_extractor import text_extractor
from app.extraction.question_segmenter import question_segmenter
from app.extraction.answer_detector import answer_detector
from app.extraction.confidence_calculator import confidence_calculator
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def run_pipeline(document_id: str, db: Session):
    """Execute document intelligence extraction pipeline for document_id."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"Document {document_id} not found for processing.")
        return

    job = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).order_by(ProcessingJob.started_at.desc()).first()
    
    try:
        # Stage 1: Validating
        doc.status = "validating"
        doc.processing_started_at = datetime.now(timezone.utc)
        if job:
            job.status = "validating"
        db.commit()

        # Stage 2: Extracting Text, Images, Tables & OCR
        doc.status = "extracting_text"
        db.commit()
        pages_data, pdf_warnings = text_extractor.extract_document(doc.storage_path, doc.content_type, doc.id)
        doc.page_count = len(pages_data)
        
        # Save Page records and organize extracted images / tables
        any_ocr_used = False
        page_records_map = {}  # page_number -> Page ORM instance
        extracted_images_by_page = {}  # page_number -> list of image dicts
        extracted_tables_by_page = {}  # page_number -> list of table dicts

        for pdata in pages_data:
            page_num = pdata["page_number"]
            if pdata["ocr_used"]:
                any_ocr_used = True

            page_rec = Page(
                document_id=doc.id,
                page_number=page_num,
                extracted_text=pdata["text"],
                ocr_used=pdata["ocr_used"],
                image_path=pdata["image_path"],
                processing_status="completed"
            )
            db.add(page_rec)
            db.flush()
            page_records_map[page_num] = page_rec

            if pdata.get("embedded_images"):
                extracted_images_by_page[page_num] = pdata["embedded_images"]
            if pdata.get("extracted_tables"):
                extracted_tables_by_page[page_num] = pdata["extracted_tables"]

        db.commit()

        if any_ocr_used:
            doc.status = "ocr_processing"
            db.commit()

        # Stage 3: Extracting Questions
        doc.status = "extracting_questions"
        db.commit()
        parsed_questions, segment_warnings = question_segmenter.segment_pages(pages_data)

        # Stage 4: Extracting Answers
        doc.status = "extracting_answers"
        db.commit()
        full_doc_text = "\n".join([p["text"] for p in pages_data])

        # Check for related answer key document
        related_doc_text = None
        rel = db.query(DocumentRelationship).filter(
            DocumentRelationship.source_document_id == doc.id,
            DocumentRelationship.relationship_type == "answer_key"
        ).first()
        if rel:
            related_pages = db.query(Page).filter(Page.document_id == rel.related_document_id).all()
            if related_pages:
                related_doc_text = "\n".join([p.extracted_text or "" for p in related_pages])

        questions_with_answers, answer_warnings = answer_detector.associate_answers(
            parsed_questions, full_doc_text, related_doc_text
        )

        all_warnings = pdf_warnings + segment_warnings + answer_warnings

        # Stage 5: Validating Confidence & Saving Questions
        doc.status = "validating"
        db.commit()

        has_high_severity_warning = False

        for q in questions_with_answers:
            # Optional LLM refinement pass
            q_refined, llm_warn = llm_service.refine_question(q)
            if llm_warn:
                all_warnings.append({
                    "warning_type": "LLM_REFINEMENT_SKIPPED",
                    "severity": "low",
                    "message": llm_warn,
                    "page_number": q_refined["source_pages"][0]
                })

            primary_page_num = q_refined["source_pages"][0]
            ocr_conf = pages_data[primary_page_num - 1].get("confidence", 1.0)
            overall_conf, signals, review_required = confidence_calculator.calculate_question_confidence(
                q_refined, ocr_confidence=ocr_conf
            )

            # Check for extracted tables on source pages
            q_tables = []
            for p_num in q_refined["source_pages"]:
                if p_num in extracted_tables_by_page:
                    q_tables.extend(extracted_tables_by_page[p_num])

            q_metadata = {
                "ocr_used": q_refined["ocr_used"],
                "signals": signals,
                "tables": q_tables
            }

            q_model = Question(
                document_id=doc.id,
                question_number=q_refined["question_number"],
                question_text=q_refined["question_text"],
                question_type=q_refined["question_type"],
                options=q_refined["options"],
                answer=q_refined["answer"],
                answer_confidence=q_refined["answer_confidence"],
                extraction_confidence=overall_conf,
                status="extracted",
                source_pages=q_refined["source_pages"],
                source_metadata=q_metadata,
                review_required=review_required
            )
            db.add(q_model)
            db.flush()  # get q_model.id

            # Associate images found on source pages
            for p_num in q_refined["source_pages"]:
                page_imgs = extracted_images_by_page.get(p_num, [])
                page_rec = page_records_map.get(p_num)

                questions_on_page = [q_item for q_item in questions_with_answers if p_num in q_item["source_pages"]]

                for img_data in page_imgs:
                    q_img = QuestionImage(
                        question_id=q_model.id,
                        page_id=page_rec.id if page_rec else None,
                        file_path=img_data["storage_key"],
                        type="image"
                    )
                    db.add(q_img)

                    if len(questions_on_page) > 1:
                        all_warnings.append({
                            "warning_type": "IMAGE_ASSOCIATION_AMBIGUOUS",
                            "severity": "medium",
                            "message": f"Embedded image on page {p_num} associated with Question {q_model.question_number} but multiple questions exist on page.",
                            "page_number": p_num,
                            "question_id": q_model.id
                        })

            if review_required:
                has_high_severity_warning = True

        # Save Extraction Warnings
        for w in all_warnings:
            w_rec = ExtractionWarning(
                document_id=doc.id,
                question_id=w.get("question_id"),
                page_number=w.get("page_number"),
                warning_type=w["warning_type"],
                message=w["message"],
                severity=w.get("severity", "medium"),
                confidence=w.get("confidence")
            )
            db.add(w_rec)

        # Final Status
        if len(all_warnings) > 0 or has_high_severity_warning:
            doc.status = "completed_with_warnings"
        else:
            doc.status = "completed"

        doc.processing_completed_at = datetime.now(timezone.utc)
        if job:
            job.status = doc.status
            job.completed_at = doc.processing_completed_at

        db.commit()
        logger.info(f"Document {document_id} processing finished with status: {doc.status}")

    except Exception as e:
        logger.exception(f"Error processing document {document_id}: {e}")
        db.rollback()
        doc.status = "failed"
        doc.error_message = str(e)
        doc.processing_completed_at = datetime.now(timezone.utc)
        if job:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = doc.processing_completed_at
        db.commit()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def process_document_task(self, document_id: str):
    """Celery task entry point."""
    db = SessionLocal()
    try:
        run_pipeline(document_id, db)
    finally:
        db.close()
