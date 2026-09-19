import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def create_clean_digital_pdf():
    pdf_path = SAMPLES_DIR / "clean_digital.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    # Page 1: Title & Questions
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "PHYSICAL SCIENCES EXAMINATION - DIGITAL PDF")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 710, "1. What is the standard unit of electrical resistance?")
    c.setFont("Helvetica", 11)
    c.drawString(70, 690, "A. Volt")
    c.drawString(70, 675, "B. Ohm")
    c.drawString(70, 660, "C. Ampere")
    c.drawString(70, 645, "D. Joule")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 600, "2. Which subatomic particle carries a negative electrical charge?")
    c.setFont("Helvetica", 11)
    c.drawString(70, 580, "A. Proton")
    c.drawString(70, 565, "B. Neutron")
    c.drawString(70, 550, "C. Electron")
    c.drawString(70, 535, "D. Positron")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 480, "Answer Key")
    c.setFont("Helvetica", 11)
    c.drawString(50, 460, "1 - B")
    c.drawString(50, 445, "2 - C")

    c.showPage()
    c.save()
    print(f"Created {pdf_path}")


def create_multipage_pdf():
    pdf_path = SAMPLES_DIR / "multipage_question.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1: Question 1 & Start of Question 2
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "COMPUTER SCIENCE TEST - MULTI-PAGE QUESTION")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 700, "1. What does CPU stand for?")
    c.setFont("Helvetica", 11)
    c.drawString(70, 680, "A. Central Processing Unit")
    c.drawString(70, 665, "B. Core Power Unit")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 610, "2. Which of the following data structures operates on a Last-In, First-Out (LIFO) basis?")
    c.setFont("Helvetica", 11)
    c.drawString(70, 590, "A. Queue")
    c.drawString(70, 575, "B. Array")

    # End of Page 1 (Question 2 options C and D are on Page 2!)
    c.showPage()

    # Page 2: Continuation of Question 2 options
    c.setFont("Helvetica", 11)
    c.drawString(70, 750, "C. Stack")
    c.drawString(70, 735, "D. Binary Tree")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 680, "Answer Keys")
    c.setFont("Helvetica", 11)
    c.drawString(50, 660, "1. A")
    c.drawString(50, 645, "2. C")

    c.showPage()
    c.save()
    print(f"Created {pdf_path}")


def create_answer_key_separate_pdf():
    pdf_path = SAMPLES_DIR / "answer_key_separate.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "OFFICIAL ANSWER KEY DOCUMENT")

    c.setFont("Helvetica", 12)
    c.drawString(50, 700, "Q1: B")
    c.drawString(50, 680, "Q2: C")
    c.drawString(50, 660, "Q3: A")

    c.showPage()
    c.save()
    print(f"Created {pdf_path}")


def create_scanned_image():
    img_path = SAMPLES_DIR / "scanned_exam.png"
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    text = (
        "SCANNED QUESTION PAPER\n\n"
        "1. What is the chemical formula for water?\n"
        "A. H2O\n"
        "B. CO2\n"
        "C. NaCl\n"
        "D. O2\n\n"
        "Answer Key\n"
        "1 - A"
    )

    d.text((50, 50), text, fill=(0, 0, 0))
    img.save(img_path)
    print(f"Created {img_path}")


def create_ambiguous_scan():
    img_path = SAMPLES_DIR / "ambiguous_scan.png"
    img = Image.new("RGB", (800, 600), color=(240, 240, 240))
    d = ImageDraw.Draw(img)

    # Missing explicit question header line to test fallback ordering
    text = (
        "Which planet is known as the Red Planet?\n"
        "A. Mars\n"
        "B. Venus\n"
        "C. Jupiter\n"
        "D. Saturn"
    )

    d.text((50, 50), text, fill=(50, 50, 50))
    img.save(img_path)
    print(f"Created {img_path}")


def create_invalid_file():
    invalid_path = SAMPLES_DIR / "invalid_file.exe"
    with open(invalid_path, "wb") as f:
        f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00")
    print(f"Created {invalid_path}")


if __name__ == "__main__":
    print("Generating sample test documents in samples/...")
    create_clean_digital_pdf()
    create_multipage_pdf()
    create_answer_key_separate_pdf()
    create_scanned_image()
    create_ambiguous_scan()
    create_invalid_file()
    print("Sample generation complete!")
