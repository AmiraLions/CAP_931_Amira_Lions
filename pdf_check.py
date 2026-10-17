"""Create and inspect a PDF using the saved reviewed brief."""

# Locate files and read the saved source records.
from pathlib import Path
import json

# Inspect the generated PDF's page count.
from io import BytesIO
from pypdf import PdfReader

# Import our PDF formatting function.
from cap_931_amira_lions.report_generator import build_report_pdf


# Run this script from the project root.
experiment_folder = Path("src/cap_931_amira_lions/experiments")

# Read the reviewed Markdown and its original evidence snapshot.
reviewed_text = (
    experiment_folder / "freedomflyer_reviewed_brief.md"
).read_text(encoding="utf-8-sig")

snapshot = json.loads(
    (experiment_folder / "experiment_03_snapshot.json")
    .read_text(encoding="utf-8-sig")
)

# Keep only the brief body.
# Sources are rebuilt from the snapshot; revision notes stay out of
# the one-pager but remain preserved in the original Markdown file.
body = reviewed_text.split("\n## Sources", 1)[0].strip()

# Remove the Markdown document title because the generator adds one.
if body.startswith("# "):
    body = body.split("\n", 1)[1].strip()

# Generate the PDF locally, with an honest editorial-status label.
pdf_bytes = build_report_pdf(
    body=body,
    sources=snapshot["sources"],
    review_status=(
        "Fictional product concept. AI draft edited after generation "
        "and checked against saved source evidence."
    ),
)

# Save the PDF in a clearly named output folder.
output_folder = Path("reports")
output_folder.mkdir(exist_ok=True)
output_path = output_folder / "FreedomFlyer_reviewed_sales_brief.pdf"
output_path.write_bytes(pdf_bytes)

# Confirm that the saved bytes form a one-page PDF.
reader = PdfReader(BytesIO(pdf_bytes))
print("PDF saved:", output_path.resolve())
print("Pages:", len(reader.pages))
print("Open the PDF to check its appearance and source links.")

# END OF FILE