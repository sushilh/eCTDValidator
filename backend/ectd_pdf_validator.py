import fitz  # PyMuPDF
import pdfplumber
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
import re

REQUIRED_SECTIONS = [
]

REQUIRED_KEYWORDS = [
    "Header Text"
]

REQUIRED_KEYWORD_VALUES = {
    "Header Text": True
}

CONTROL_TYPE_MAP = {
    "Tx": "Text Field",
    "Btn": "Button / Checkbox",
    "Ch": "Dropdown",
    "Sig": "Signature Field"
}

def extract_text_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def extract_text_pdfplumber(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_pdfminer(pdf_path):
    return extract_text(pdf_path)

def check_keyword_on_each_page(pdf_path, keywords):
    header_missing_pages = []
    doc = fitz.open(pdf_path)
    page_errors = {}
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        for keyword in keywords:
            match = re.search(rf"{re.escape(keyword)}\s*:\s*(\S.*)?", text)
            if not match or not match.group(1).strip():
                if keyword == 'Header Text':
                    header_missing_pages.append(page_num)
                page_errors.setdefault(keyword, []).append(page_num)
    page_errors['Header Text Missing Pages'] = header_missing_pages
    return page_errors

def check_live_controls_on_each_page(pdf_path):
    doc = fitz.open(pdf_path)
    missing_controls = []
    control_details = {}
    for page_num, page in enumerate(doc, start=1):
        widgets = page.widgets()
        if not widgets:
            missing_controls.append(page_num)
        else:
            readable = []
            for w in widgets:
                if w.field_type:
                    control_type = CONTROL_TYPE_MAP.get(w.field_type, f"Unknown ({w.field_type})")
                    readable.append(f"{control_type}: {w.field_name}")
            control_details[page_num] = readable
    return missing_controls, control_details

def check_pdf_compliance(pdf_path):
    doc = fitz.open(pdf_path)
    errors = []
    info = {}

    # 1. PDF version
    version_str = doc.metadata.get("format", "")
    info['pdf_version'] = version_str
    match = re.search(r"PDF (\d\.\d+)", version_str)
    if match:
        version = float(match.group(1))
        if not (1.4 <= version <= 1.7):
            errors.append(f"PDF version {version} is not between 1.4 and 1.7")
    else:
        errors.append("Unable to determine PDF version")

    # 2. Bookmarks for docs > 2 pages
    if len(doc) > 2 and not doc.get_toc():
        errors.append("Bookmarks are required for documents longer than 2 pages")

    # 3. Hyperlink check
    has_links = any(len(page.get_links()) > 0 for page in doc)
    if not has_links:
        errors.append("No live hyperlinks found in document")

    # 4. View mode check
    page_mode = doc.metadata.get("page_mode", "")
    if page_mode != "/UseOutlines":
        errors.append("PDF view mode is not set to 'Bookmarks Panel and Page'")

    # 5. Metadata check
    metadata = doc.metadata
    info['metadata'] = metadata
    required_meta = ['title', 'author']
    for key in required_meta:
        if not metadata.get(key):
            errors.append(f"Missing PDF metadata field: {key}")

    # 6. Fonts must be embedded — using pdfminer
    try:
        with open(pdf_path, 'rb') as f:
            parser = PDFParser(f)
            document = PDFDocument(parser)
            if not document.is_extractable:
                errors.append("PDF text extraction is not allowed.")
            fonts_embedded = True
            for page in PDFPage.create_pages(document):
                if '/Resources' in page.attrs and '/Font' in page.attrs['/Resources']:
                    fonts = page.attrs['/Resources']['/Font'].resolve()
                    for font_ref in fonts.values():
                        font = font_ref.resolve()
                        if '/FontDescriptor' in font and '/FontFile' not in font['/FontDescriptor']:
                            fonts_embedded = False
            if not fonts_embedded:
                errors.append("One or more fonts are not embedded in the PDF.")
    except Exception as e:
        errors.append("Font embedding check failed: {str(e)}")

    # 7. Page numbers visible (very basic check: look for numeric footer)
    page_number_issues = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if not re.search(rf"\b{i+1}\b", text):
            page_number_issues.append(i+1)
    if page_number_issues:
        errors.append(f"Page number not found on pages: {page_number_issues}")

    return errors, info

def validate_ectd_pdf(text, pdf_path):
    lines = text.splitlines()
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in text]
    missing_keywords = [kw for kw in REQUIRED_KEYWORDS if kw not in text]
    missing_keyword_values = []

    for keyword, check_value in REQUIRED_KEYWORD_VALUES.items():
        found = False
        for line in lines:
            if re.search(rf"^{re.escape(keyword)}\s*:\s*(.+)$", line, re.IGNORECASE):
                value = re.search(rf"^{re.escape(keyword)}\s*:\s*(.+)$", line, re.IGNORECASE).group(1).strip()
                if value:
                    found = True
                break
        if not found:
            missing_keyword_values.append(keyword)

    per_page_errors = check_keyword_on_each_page(pdf_path, REQUIRED_KEYWORD_VALUES.keys())
    missing_controls, control_details = check_live_controls_on_each_page(pdf_path)
    pdf_errors, pdf_info = check_pdf_compliance(pdf_path)

    report = {
        "status": "PASS" if not (missing_sections or missing_keywords or missing_keyword_values or per_page_errors or missing_controls or pdf_errors) else "FAIL",
        "details": {
            "missing_sections": missing_sections,
            "missing_keywords": missing_keywords,
            "missing_values": missing_keyword_values,
            "per_page_value_errors": per_page_errors,
            "missing_controls_pages": missing_controls,
            "live_controls": control_details,
            "pdf_compliance_errors": pdf_errors,
            "pdf_info": pdf_info,
            "validation_summary": (
                f"Missing Sections: {len(missing_sections)}, "
                f"Missing Keywords: {len(missing_keywords)}, "
                f"Missing Values: {len(missing_keyword_values)}, "
                f"Header Missing for Pages: {sum(len(p) for p in per_page_errors.values())}, "
                f"Pages Missing Controls: {len(missing_controls)}, "
                f"PDF Compliance Issues: {len(pdf_errors)}"
            )
        }
    }

    if missing_sections:
        report["details"]["section_errors"] = [f"Missing required section: '{s}'" for s in missing_sections]
    if missing_keywords:
        report["details"]["keyword_errors"] = [f"Missing required keyword: '{k}'" for k in missing_keywords]
    if missing_keyword_values:
        report["details"]["value_errors"] = [f"Missing value for keyword: '{k}'" for k in missing_keyword_values]

    return report

def combine_text(pdf_path):
    text1 = extract_text_pymupdf(pdf_path)
    text2 = extract_text_pdfplumber(pdf_path)
    text3 = extract_text_pdfminer(pdf_path)
    combined = "\n".join([text1, text2, text3])
    return combined

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python ectd_pdf_validator.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print("Extracting text using PyMuPDF, pdfplumber, and pdfminer.six...")
    extracted_text = combine_text(pdf_path)

    print("Running eCTD validation...\n")
    validation_result = validate_ectd_pdf(extracted_text, pdf_path)
    print(json.dumps(validation_result, indent=2))
