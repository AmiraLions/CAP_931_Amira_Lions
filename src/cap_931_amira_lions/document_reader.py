"""
Extract product information from TXT files and text-based PDFs.

The interface will pass the filename and file contents to this module.
Files are read in memory rather than saved to the project folder.
"""

# BytesIO lets the PDF reader treat uploaded bytes like an open file.
from io import BytesIO

# PdfReader extracts text from PDF pages.
from pypdf import PdfReader


# Limit uploads and extraction work for this prototype.
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_TEXT_CHARACTERS = 20000


def read_document(filename, file_bytes):
    """
    Return extracted text, warnings, and any error.

    filename is the uploaded file's name.
    file_bytes contains its raw contents.

    An error means the document should not be used as product context.
    Warnings explain limitations, such as truncated text.
    """

    # Use the same result structure for successful and failed reads.
    result = {
        "filename": filename,
        "text": "",
        "warnings": [],
        "error": None,
    }

    # Reject empty or oversized files before parsing them.
    if not file_bytes:
        result["error"] = "The uploaded file is empty."
        return result

    if len(file_bytes) > MAX_FILE_BYTES:
        result["error"] = "Please upload a file no larger than 5 MB."
        return result

    # Only the filename extension is used to select the reader.
    # The parser still needs to verify that the contents are readable.
    extension = filename.rsplit(".", 1)[-1].lower()

    try:
        if extension == "txt":
            # UTF-8 is our supported text encoding.
            # utf-8-sig also handles a UTF-8 byte-order mark.
            try:
                text = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                result["error"] = (
                    "This TXT file is not UTF-8. Save it as UTF-8 "
                    "in your editor and upload it again."
                )
                return result

        elif extension == "pdf":
            # Read the PDF directly from memory.
            reader = PdfReader(BytesIO(file_bytes))

            # Reject encrypted PDFs rather than asking for passwords.
            if reader.is_encrypted:
                result["error"] = (
                    "Encrypted PDFs are not supported. "
                    "Upload an unencrypted copy you are authorized to use."
                )
                return result

            if len(reader.pages) > MAX_PDF_PAGES:
                result["error"] = (
                    "Please upload a PDF with no more than 30 pages."
                )
                return result

            # Some PDF pages contain images but no extractable text.
            # Keep track of those pages so omissions are visible.
            parts = []
            empty_pages = []

            for number, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""

                if page_text.strip():
                    parts.append(
                        f"[Page {number}]\n{page_text.strip()}"
                    )
                else:
                    empty_pages.append(number)

            text = "\n\n".join(parts)

            if empty_pages:
                result["warnings"].append(
                    "No text was extracted from PDF page(s): "
                    + ", ".join(map(str, empty_pages))
                    + ". They may need OCR or contain no text."
                )

        else:
            result["error"] = "Please upload a PDF or TXT file."
            return result

        # Whitespace alone is not usable product information.
        if not text.strip():
            result["error"] = (
                "No usable text was found. Scanned PDFs require OCR, "
                "which this prototype does not provide."
            )
            return result

        # Limit how much document text can later enter a model request.
        # Characters and model tokens are different measurements.
        text = text.strip()

        if len(text) > MAX_TEXT_CHARACTERS:
            result["warnings"].append(
                "Only the first 20,000 characters were retained. "
                "Review the preview for omitted product information."
            )

        result["text"] = text[:MAX_TEXT_CHARACTERS]

    except Exception:
        # Third-party PDF parsers can raise several kinds of errors.
        # Catch failures at this file-reading boundary so a malformed
        # upload produces a message instead of crashing the interface.
        # Do not show document contents or raw exception details.
        result["error"] = (
            "The document could not be read. It may be damaged "
            "or use an unsupported format."
        )

    return result


# END OF FILE