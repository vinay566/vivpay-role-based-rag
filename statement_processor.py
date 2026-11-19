
import io
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


MAX_TEXT_LENGTH = 150_000


def extract_pdf(file_bytes):
    """Extract text from a PDF bank statement."""

    reader = PdfReader(io.BytesIO(file_bytes))

    if reader.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported yet.")

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""

        if page_text.strip():
            pages.append(
                f"Page {page_number}:\n{page_text}"
            )

    return "\n\n".join(pages)



def extract_csv(file_bytes):

    encodings = [
        "utf-8-sig",
        "cp1252",
        "latin1"
    ]

    dataframe = None

    for encoding in encodings:

        try:
            dataframe = pd.read_csv(
                io.BytesIO(file_bytes),
                dtype=str,
                encoding=encoding
            )

            print(f"CSV successfully decoded using {encoding}")
            break

        except UnicodeDecodeError:
            continue

    if dataframe is None:
        raise ValueError(
            "Unable to decode the CSV file. "
            "Please check its encoding."
        )

    dataframe = dataframe.fillna("")

    return dataframe.to_string(index=False)



def extract_excel(file_bytes):
    """Extract transaction data from an Excel statement."""

    sheets = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=None,
        dtype=str
    )

    extracted_sheets = []

    for sheet_name, dataframe in sheets.items():

        dataframe = dataframe.fillna("")

        extracted_sheets.append(
            f"Sheet: {sheet_name}\n"
            f"{dataframe.to_string(index=False)}"
        )

    return "\n\n".join(extracted_sheets)


def process_statement(filename, file_bytes):
    """
    Extract text from PDF, CSV or Excel.
    Processes the uploaded bytes without saving the file.
    """

    extension = Path(filename).suffix.lower()

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    if extension == ".pdf":
        text = extract_pdf(file_bytes)

    elif extension == ".csv":
        text = extract_csv(file_bytes)

    elif extension in [".xlsx", ".xls"]:
        if extension == ".xls":
            raise ValueError(
                "Please upload an .xlsx file instead of .xls."
            )

        text = extract_excel(file_bytes)

    else:
        raise ValueError(
            "Unsupported file format. Upload PDF, CSV or XLSX."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found in the bank statement."
        )

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            "Statement is too large to process. "
            "Please upload a smaller statement."
        )

    return text
