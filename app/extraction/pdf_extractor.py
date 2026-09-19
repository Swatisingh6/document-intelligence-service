import os
import logging
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from PIL import Image

from app.ocr.ocr_engine import ocr_engine, OcrProvider
from app.storage.storage_service import storage_service
from app.extraction.image_table_extractor import image_table_extractor

logger = logging.getLogger(__name__)


class DocumentTextExtractor:
    """Extracts raw page text, embedded images, and tables from digital PDFs, scanned PDFs, and image files."""

    def __init__(self, ocr_provider: OcrProvider = ocr_engine):
        self.ocr_provider = ocr_provider

    def extract_document(self, storage_key: str, content_type: str, doc_id: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract text page-by-page.
        Returns tuple: (pages_data, extraction_warnings)
        """
        file_path = storage_service.get_file_path(storage_key)
        ext = os.path.splitext(file_path)[1].lower()

        pages_data = []
        warnings = []

        if ext == ".pdf":
            pages_data, warnings = self._process_pdf(file_path, doc_id)
        elif ext in [".jpg", ".jpeg", ".png"]:
            pages_data, warnings = self._process_image_file(file_path)
        else:
            raise ValueError(f"Unsupported file type for extraction: {ext}")

        return pages_data, warnings

    def _process_pdf(self, pdf_path: str, doc_id: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        pages_data = []
        warnings = []
        doc = fitz.open(pdf_path)

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Try native PDF text extraction
            native_text = page.get_text("text").strip()
            ocr_used = False
            ocr_conf = 1.0

            # 2. Extract embedded images & tables while doc is open
            embedded_images = image_table_extractor.extract_images_from_page(page, doc_id, page_num)
            extracted_tables, table_warns = image_table_extractor.extract_tables_from_page(page, page_num)
            if table_warns:
                warnings.extend(table_warns)

            # 3. Check if text is sufficient or if it's a scanned page
            if len(native_text) < 50:
                logger.info(f"Page {page_num} native text sparse ({len(native_text)} chars). Falling back to OCR.")
                
                if not self.ocr_provider.is_available():
                    warnings.append({
                        "warning_type": "OCR_UNAVAILABLE",
                        "message": f"Page {page_num} requires OCR but Tesseract system binary is not available.",
                        "severity": "high",
                        "page_number": page_num
                    })
                else:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img_bytes = pix.tobytes("png")

                    ocr_text, conf = self.ocr_provider.process_image(img_bytes)
                    if ocr_text.strip():
                        native_text = ocr_text.strip()
                        ocr_used = True
                        ocr_conf = conf

            pages_data.append({
                "page_number": page_num,
                "text": native_text,
                "ocr_used": ocr_used,
                "confidence": ocr_conf,
                "image_path": None,
                "embedded_images": embedded_images,
                "extracted_tables": extracted_tables
            })

        doc.close()
        return pages_data, warnings

    def _process_image_file(self, img_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        warnings = []
        if not self.ocr_provider.is_available():
            warnings.append({
                "warning_type": "OCR_UNAVAILABLE",
                "message": "Image document requires OCR but Tesseract system binary is not available.",
                "severity": "high",
                "page_number": 1
            })
            ocr_text, conf = "", 0.0
        else:
            ocr_text, conf = self.ocr_provider.process_image(img_path)

        pages_data = [{
            "page_number": 1,
            "text": ocr_text,
            "ocr_used": True,
            "confidence": conf,
            "image_path": None,
            "embedded_images": [],
            "extracted_tables": []
        }]
        return pages_data, warnings


text_extractor = DocumentTextExtractor()
