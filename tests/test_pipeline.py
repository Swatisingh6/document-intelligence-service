import io
from PIL import Image
from app.extraction.question_segmenter import question_segmenter
from app.extraction.option_extractor import option_extractor
from app.extraction.answer_detector import answer_detector
from app.extraction.confidence_calculator import confidence_calculator
from app.extraction.image_table_extractor import image_table_extractor
from app.ocr.ocr_engine import TesseractOcrProvider


def test_question_segmenter_multi_page():
    pages_data = [
        {
            "page_number": 1,
            "text": "1. What is 2 + 2?\nA. 3\nB. 4\n\n2. Which planet is closest to the sun?\nA. Earth\nB. Venus",
            "ocr_used": False,
            "confidence": 1.0
        },
        {
            "page_number": 2,
            "text": "C. Mercury\nD. Mars\n\nAnswer Key\n1 - B\n2 - C",
            "ocr_used": False,
            "confidence": 1.0
        }
    ]

    questions, warnings = question_segmenter.segment_pages(pages_data)
    assert len(questions) == 2

    assert questions[0]["question_number"] == "1"
    assert questions[0]["source_pages"] == [1]

    assert questions[1]["question_number"] == "2"
    assert questions[1]["source_pages"] == [1, 2]
    assert len(questions[1]["options"]) == 4
    opt_keys = [o["key"] for o in questions[1]["options"]]
    assert opt_keys == ["A", "B", "C", "D"]


def test_option_extractor_expanded_formats():
    # Test Bracketed options: [A], [B]
    text_bracket = "1. Question stem\n[A] Option 1\n[B] Option 2"
    _, opts_bracket = option_extractor.extract_options(text_bracket)
    assert len(opts_bracket) == 2
    assert opts_bracket[0]["key"] == "A"
    assert opts_bracket[1]["key"] == "B"

    # Test Parentheses options: (a), (b)
    text_paren = "2. Question stem\n(a) Alpha\n(b) Beta"
    _, opts_paren = option_extractor.extract_options(text_paren)
    assert len(opts_paren) == 2
    assert opts_paren[0]["key"] == "A"
    assert opts_paren[1]["key"] == "B"

    # Test Roman numerals options: (i), (ii)
    text_roman = "3. Question stem\n(i) First\n(ii) Second"
    _, opts_roman = option_extractor.extract_options(text_roman)
    assert len(opts_roman) == 2
    assert opts_roman[0]["key"] == "I"
    assert opts_roman[1]["key"] == "II"

    # Test Numbered parenthesis options: 1), 2)
    text_num = "4. Question stem\n1) Choice One\n2) Choice Two"
    _, opts_num = option_extractor.extract_options(text_num)
    assert len(opts_num) == 2
    assert opts_num[0]["key"] == "1"
    assert opts_num[1]["key"] == "2"


def test_answer_detector_association():
    questions = [
        {"question_number": "1", "source_pages": [1]},
        {"question_number": "2", "source_pages": [1]}
    ]
    doc_text = "Question Paper\nAnswer Key\n1 - A\n2 - D"

    qs_with_answers, warnings = answer_detector.associate_answers(questions, doc_text)
    assert qs_with_answers[0]["answer"] == "A"
    assert qs_with_answers[1]["answer"] == "D"


def test_confidence_calculator():
    question = {
        "question_number": "1",
        "question_type": "mcq",
        "options": [{"key": "A", "text": "a"}, {"key": "B", "text": "b"}, {"key": "C", "text": "c"}, {"key": "D", "text": "d"}],
        "answer": "B",
        "answer_confidence": 0.95,
        "ocr_used": False,
        "is_generated_number": False
    }

    score, signals, review_req = confidence_calculator.calculate_question_confidence(question)
    assert score >= 0.85
    assert not review_req


def test_ocr_missing_binary_graceful_handling():
    # Pass custom non-existent tesseract binary path
    provider = TesseractOcrProvider(tesseract_cmd="non_existent_tesseract_cmd_path_12345")
    assert not provider.is_available()

    # Create valid dummy PNG image bytes
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(255, 255, 255))
    img.save(buf, format="PNG")
    valid_bytes = buf.getvalue()

    text, conf = provider.process_image(valid_bytes)
    assert text == ""
    assert conf == 0.0


def test_table_extractor_interface():
    # Verify table extractor handles dummy page object gracefully
    tables, warnings = image_table_extractor.extract_tables_from_page(None, page_num=1)
    assert tables == []
    assert warnings == []
