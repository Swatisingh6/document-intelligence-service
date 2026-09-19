import re
import logging
from typing import List, Dict, Any, Tuple
from app.extraction.option_extractor import option_extractor

logger = logging.getLogger(__name__)


class QuestionSegmenter:
    """Segments raw page text into structured question candidate blocks."""

    # Regex patterns matching question headers
    HEADER_PATTERNS = [
        # Q1. / Q.1 / Q1: / Question 1: / Question No. 1 / Question 1.
        r'^(?:Q|Q\.|Question|Question\s+No\.|Question\s+Num\.)\s*(\d+)[\:\.\-\s]',
        # 1. / 01. / 10.
        r'^(\d{1,3})\.\s+',
        # 1) / 2)
        r'^(\d{1,3})\)\s+',
        # (1) / (2)
        r'^\((\d{1,3})\)\s+',
    ]

    # Regex detecting answer key header sections to avoid segmenting answer key into questions
    ANSWER_KEY_HEADER_PATTERN = r'^(?:Answer\s+Keys?|Correct\s+Answers?|Solutions?|Ans\.?)\b'

    def segment_pages(self, pages_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Segment page texts into a list of parsed question dictionary blocks and warnings.
        """
        raw_questions: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        current_q: Optional[Dict[str, Any]] = None
        generated_counter = 1

        for page_data in pages_data:
            page_num = page_data["page_number"]
            page_text = page_data["text"] or ""
            ocr_used = page_data.get("ocr_used", False)

            lines = page_text.split("\n")
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                # Check if this line is an Answer Key section header
                if re.match(self.ANSWER_KEY_HEADER_PATTERN, stripped, re.IGNORECASE):
                    # Save current question if any
                    if current_q:
                        raw_questions.append(current_q)
                        current_q = None
                    # Stop treating remaining lines on this page as question stems (they belong to answer key)
                    break

                # Check if line matches any question header pattern
                num_found = None
                for pat in self.HEADER_PATTERNS:
                    m = re.match(pat, stripped, re.IGNORECASE)
                    if m:
                        num_found = m.group(1)
                        break

                if num_found:
                    # Finalize current in-flight question
                    if current_q:
                        raw_questions.append(current_q)

                    current_q = {
                        "question_number": num_found,
                        "raw_text": stripped,
                        "source_pages": [page_num],
                        "ocr_used": ocr_used,
                        "is_generated_number": False
                    }
                else:
                    # Continuation line
                    if current_q:
                        # Cross-page continuation check
                        if page_num not in current_q["source_pages"]:
                            current_q["source_pages"].append(page_num)
                            warnings.append({
                                "warning_type": "QUESTION_CONTINUES_NEXT_PAGE",
                                "message": f"Question {current_q['question_number']} spans from page {current_q['source_pages'][0]} to page {page_num}",
                                "severity": "low",
                                "page_number": page_num
                            })

                        current_q["raw_text"] += "\n" + stripped
                    else:
                        # Text before any question header (e.g. unnumbered initial question)
                        # Generate internal fallback question number
                        q_num_str = f"AUTO_{generated_counter}"
                        generated_counter += 1
                        current_q = {
                            "question_number": q_num_str,
                            "raw_text": stripped,
                            "source_pages": [page_num],
                            "ocr_used": ocr_used,
                            "is_generated_number": True
                        }
                        warnings.append({
                            "warning_type": "MISSING_QUESTION_NUMBER",
                            "message": f"Question start on page {page_num} missing explicit numbering. Generated identifier '{q_num_str}'",
                            "severity": "medium",
                            "page_number": page_num
                        })

        if current_q:
            raw_questions.append(current_q)

        # Process each raw question block: extract options & stem
        final_questions = []
        for q in raw_questions:
            raw_txt = q["raw_text"]
            stem_text, options = option_extractor.extract_options(raw_txt)

            # Heuristic question type determination
            q_type = "unknown"
            if len(options) >= 2:
                q_type = "mcq"
            elif any(word in stem_text.lower() for word in ["true or false", "true/false", "t/f"]):
                q_type = "true_false"
            elif "___" in stem_text or "..." in stem_text:
                q_type = "fill_blank"
            elif len(stem_text.split()) > 30:
                q_type = "descriptive"
            else:
                q_type = "short_answer"

            if len(options) == 0 and q_type == "mcq":
                warnings.append({
                    "warning_type": "OPTIONS_INCOMPLETE",
                    "message": f"Question {q['question_number']} classified as MCQ but zero options extracted",
                    "severity": "high",
                    "page_number": q["source_pages"][0]
                })

            final_questions.append({
                "question_number": q["question_number"],
                "question_text": stem_text,
                "question_type": q_type,
                "options": options,
                "source_pages": q["source_pages"],
                "ocr_used": q["ocr_used"],
                "is_generated_number": q["is_generated_number"]
            })

        return final_questions, warnings


question_segmenter = QuestionSegmenter()
