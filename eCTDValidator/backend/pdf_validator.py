import fitz  # PyMuPDF
import pdfplumber
import pikepdf
from PyPDF2 import PdfReader
import json
import logging
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_ectd_compliance(pdf_path):
    """ Validate the PDF against eCTD (Electronic Common Technical Document) compliance rules."""
    logging.info("Starting eCTD compliance check")
    try:
        reader = PdfReader(pdf_path)
        metadata = reader.metadata
        logging.info("Extracted metadata from PDF")

        required_metadata = ["/Title", "/Author", "/Subject", "/Keywords"]
        missing_metadata = [field for field in required_metadata if field not in metadata or not metadata[field]]
        logging.info(f"Missing metadata fields: {missing_metadata}")

        # doc = fitz.open(pdf_path)
        # fonts_embedded = all(font.get("embedded", False) for page in doc for font in page.get_fonts())
        # logging.info(f"Fonts embedded: {fonts_embedded}")

        doc = fitz.open(pdf_path)
        pdf_version = float(reader.pdf_header[5:])
        logging.info(f"PDF Version: {pdf_version}")

        # is_tagged = any("/StructTreeRoot" in page.get_text("dict") for page in doc.pages)
        # logging.info(f"PDF is tagged: {is_tagged}")

        pdf = pikepdf.Pdf.open(pdf_path)
        is_unlocked = not pdf.is_encrypted
        logging.info(f"PDF is unlocked: {is_unlocked}")

        contains_text = any(page.get_text() for page in doc.pages)
        logging.info(f"PDF contains extractable text: {contains_text}")

        is_compliant = (
                not missing_metadata and pdf_version >= 1.4 and is_unlocked and contains_text
        )

        logging.info("eCTD compliance check completed")
        return {
            "ectdValid": is_compliant,
            "missingMetadata": missing_metadata,

            "pdfVersion": pdf_version,

            "unlockedPDF": is_unlocked,
            "containsText": contains_text
        }
    except Exception as e:
        logging.error(f"Error in eCTD compliance check: {str(e)}")
        return {"ectdValid": False, "error": str(e)}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_pdf(file_path):
    logging.info(f"Validating PDF: {file_path}")
    report = {
        "file": file_path,
        "valid": True,
        "errors": []
    }

    try:
        doc = fitz.open(file_path)
        report["page_count"] = len(doc)
        logging.info(f"PDF contains {len(doc)} pages")
    except Exception as e:
        logging.error("File error: " + str(e))
        report["valid"] = False
        report["errors"].append(f"File error: {str(e)}")
        return report

    try:
        with pdfplumber.open(file_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            if not text.strip():
                report["errors"].append("No extractable text found.")
                logging.warning("No extractable text found in PDF")
    except Exception as e:
        logging.error("Text extraction error: " + str(e))
        report["errors"].append(f"Text extraction error: {str(e)}")

    try:
        pdf = pikepdf.Pdf.open(file_path)
        report["encrypted"] = pdf.is_encrypted
        logging.info(f"PDF encryption status: {pdf.is_encrypted}")
    except Exception as e:
        logging.error("Security check error: " + str(e))
        report["errors"].append(f"Security check error: {str(e)}")

    try:
        reader = PdfReader(file_path)
        metadata = reader.metadata
        report["metadata"] = metadata or "No metadata found"
        logging.info("Metadata extracted successfully")
    except Exception as e:
        logging.error("Metadata extraction error: " + str(e))
        report["errors"].append(f"Metadata error: {str(e)}")

    ectd_result = validate_ectd_compliance(file_path)
    report.update(ectd_result)

    if report["errors"]:
        report["valid"] = False
        logging.warning("Validation completed with errors")
    else:
        logging.info("Validation completed successfully")

    return json.dumps(report, indent=4)


@app.post("/validate")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    logging.info(f"Receiving file: {file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    result = validate_pdf(file_path)
    os.remove(file_path)  # Clean up after processing
    logging.info(f"File {file.filename} validation completed and deleted from temp storage")
    return json.loads(result)


if __name__ == "__main__":
    logging.info("Starting PDF Validator API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
