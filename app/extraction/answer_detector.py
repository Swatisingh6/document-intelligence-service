import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class AnswerDetector:
    """Detects answer keys within documents and links them to questions."""

    LINE_PATTERNS = [
        # 1 - A / 1-A / 1 - (A) / Q1 - A / Q1. A / 1. A / 1) A
        r'^(?:Q|Q\.)?\s*(\d+)\s*[\-\:\.\)]\s*\(?([A-Ea-e])\)?(?:\s+|$)'
    ]

    def extract_answer_map(self, text_content: str) -> Dict[str, str]:
        """
        Scan full document text or answer-key document text line by line and build a mapping:
        {"1": "A", "2": "C", ...}
        """
        answer_map: Dict[str, str] = {}
        if not text_content:
            return answer_map

        for line in text_content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            for pattern in self.LINE_PATTERNS:
                match = re.search(pattern, stripped, re.IGNORECASE)
                if match:
                    q_num = match.group(1).strip()
                    ans_char = match.group(2).strip().upper()
                    if q_num not in answer_map:
                        answer_map[q_num] = ans_char
                    break

        return answer_map

    def associate_answers(
        self,
        questions: List[Dict[str, Any]],
        document_text: str,
        related_doc_text: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Associate answers with questions.
        Returns (updated_questions, warnings).
        """
        warnings: List[Dict[str, Any]] = []

        # 1. Extract answers from main document text
        answer_map = self.extract_answer_map(document_text)

        # 2. Merge with related answer key document text if provided
        if related_doc_text:
            related_map = self.extract_answer_map(related_doc_text)
            answer_map.update(related_map)

        for q in questions:
            q_num = str(q["question_number"]).strip()
            # Try direct match or regex digit extraction from question number
            clean_num = re.sub(r'\D', '', q_num)

            matched_answer = None
            if q_num in answer_map:
                matched_answer = answer_map[q_num]
            elif clean_num and clean_num in answer_map:
                matched_answer = answer_map[clean_num]

            if matched_answer:
                q["answer"] = matched_answer
                q["answer_confidence"] = 0.95
            else:
                q["answer"] = None
                q["answer_confidence"] = 0.0
                warnings.append({
                    "warning_type": "ANSWER_UNMATCHED",
                    "severity": "medium",
                    "message": f"Answer key entry could not be associated with question {q['question_number']}",
                    "confidence": 0.40,
                    "page_number": q["source_pages"][0] if q.get("source_pages") else None
                })

        return questions, warnings


answer_detector = AnswerDetector()
