import os
import io
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Union
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class OcrProvider(ABC):
    """Abstract interface for OCR providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if OCR binary/service is available."""
        pass

    @abstractmethod
    def process_image(self, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> Tuple[str, float]:
        """
        Process image and return (extracted_text, confidence_score).
        confidence_score is normalized between 0.0 and 1.0.
        """
        pass


class TesseractOcrProvider(OcrProvider):
    """Local Tesseract OCR implementation with OpenCV preprocessing and deskew."""

    def __init__(self, tesseract_cmd: str = settings.TESSERACT_CMD):
        self.tesseract_cmd = tesseract_cmd
        if pytesseract and hasattr(pytesseract, 'pytesseract'):
            try:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            except Exception as e:
                logger.warning(f"Could not configure pytesseract cmd: {e}")

    def is_available(self) -> bool:
        if pytesseract is None:
            return False
        try:
            # Check if tesseract binary can be called
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def _preprocess_image(self, cv_img: np.ndarray) -> np.ndarray:
        """Apply OpenCV grayscale, denoising, thresholding, and deskew."""
        if cv2 is None or cv_img is None:
            return cv_img

        if len(cv_img.shape) == 3:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_img

        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        try:
            coords = np.column_stack(np.where(thresh == 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                if abs(angle) > 0.5 and abs(angle) < 45:
                    (h, w) = thresh.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    thresh = cv2.warpAffine(
                        thresh, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
        except Exception as e:
            logger.debug(f"Deskew skipped: {e}")

        return thresh

    def process_image(self, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> Tuple[str, float]:
        pil_img = None
        cv_img = None

        if isinstance(image_input, str):
            if os.path.exists(image_input):
                pil_img = Image.open(image_input)
                if cv2:
                    cv_img = cv2.imread(image_input)
        elif isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input))
            if cv2:
                nparr = np.frombuffer(image_input, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_input, Image.Image):
            pil_img = image_input
            if cv2:
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            cv_img = image_input
            pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

        if pil_img is None:
            return "", 0.0

        if cv_img is not None and cv2 is not None:
            try:
                processed_cv = self._preprocess_image(cv_img)
                pil_img = Image.fromarray(processed_cv)
            except Exception as e:
                logger.warning(f"OpenCV preprocessing error: {e}")

        if not self.is_available():
            logger.warning("Tesseract binary not available. OCR text extraction skipped.")
            return "", 0.0

        try:
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            text_lines = []
            confidences = []

            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                if text:
                    text_lines.append(text)
                    if conf > 0:
                        confidences.append(conf)

            full_text = pytesseract.image_to_string(pil_img)
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.70
            return full_text.strip(), round(avg_conf, 2)

        except Exception as e:
            logger.warning(f"Tesseract binary execution failed ({e}). Returning empty OCR result.")
            return "", 0.0


class MockFallbackOcrProvider(OcrProvider):
    """Fallback OCR provider when external OCR system binaries are absent."""

    def is_available(self) -> bool:
        return True

    def process_image(self, image_input: Union[str, bytes, Image.Image, np.ndarray]) -> Tuple[str, float]:
        return "Scanned document text content fallback.", 0.75


ocr_engine: OcrProvider = TesseractOcrProvider()
