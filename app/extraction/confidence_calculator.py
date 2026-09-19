from typing import Dict, Any, Tuple
from app.core.config import settings


class ConfidenceCalculator:
    """Calculates explainable confidence score between 0.0 and 1.0."""

    def calculate_question_confidence(
        self,
        question: Dict[str, Any],
        ocr_confidence: float = 1.0
    ) -> Tuple[float, Dict[str, float], bool]:
        """
        Calculate overall score, breakdown signal dictionary, and review_required boolean flag.
        """
        signals: Dict[str, float] = {}

        # 1. OCR signal
        if question.get("ocr_used", False):
            signals["ocr"] = max(0.5, ocr_confidence)
        else:
            signals["ocr"] = 1.0

        # 2. Question Boundary signal
        if question.get("is_generated_number", False):
            signals["question_boundary"] = 0.60
        else:
            signals["question_boundary"] = 0.95

        # 3. Options structure signal
        options = question.get("options") or []
        q_type = question.get("question_type", "unknown")

        if q_type == "mcq":
            if len(options) >= 4:
                signals["options"] = 1.0
            elif len(options) >= 2:
                signals["options"] = 0.75
            else:
                signals["options"] = 0.40
        else:
            signals["options"] = 1.0

        # 4. Answer mapping signal
        if question.get("answer"):
            signals["answer_mapping"] = float(question.get("answer_confidence", 0.95))
        else:
            signals["answer_mapping"] = 0.50

        # Weighted calculation
        overall = (
            signals["ocr"] * 0.25 +
            signals["question_boundary"] * 0.30 +
            signals["options"] * 0.25 +
            signals["answer_mapping"] * 0.20
        )

        overall = round(overall, 2)
        review_required = overall < settings.MEDIUM_CONFIDENCE_THRESHOLD or question.get("is_generated_number", False)

        return overall, signals, review_required


confidence_calculator = ConfidenceCalculator()
