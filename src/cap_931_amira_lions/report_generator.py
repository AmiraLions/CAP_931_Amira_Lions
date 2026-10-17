"""
Create a one-page PDF from a sales brief and its source records.

This module formats existing text. It does not call GPT, retrieve
websites, or verify whether factual claims are supported.
"""

# BytesIO stores the generated PDF in memory.
from io import BytesIO

# Escape special characters before passing text to ReportLab.
from html import escape

# Regular expressions identify headings and paragraph boundaries.
import re

# Check the number of pages in the completed PDF.
from pypdf import PdfReader

# ReportLab supplies page dimensions, colors, styles, and layout tools.
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.doctemplate import LayoutError

# Reuse our citation parser to identify referenced source records.
# Importing it does not make an API request.
from cap_931_amira_lions.llm_client import citation_ids


def plain_text(value):
    """Prepare ordinary Markdown text for PDF paragraphs."""

    # Use standard punctuation supported by the built-in PDF font.
    value = value.replace("’", "'").replace("‘", "'")
    value = value.replace("“", '"').replace("”", '"')
    value = value.replace("–", "-").replace("—", "-")

    # Remove simple Markdown bold markers.
    # Escape HTML-like characters so source text is displayed as text.
    return escape(value.replace("**", ""))


def build_report_pdf(
    body,
    sources,
    title="FreedomFlyer Sales Account Brief",
    review_status="AI-generated draft; human factual review required.",
):
    """
    Return PDF bytes containing one page.

    body contains the brief WITHOUT its appended Sources section.
    sources contains dictionaries with id, title, and url fields.
    review_status describes the report's actual review state.

    Raise ValueError if content is empty, citations are unknown,
    or the complete content cannot fit at the permitted font sizes.
    """

    if not body.strip():
        raise ValueError("The report body is empty.")

    # Do not silently remove an appended source list.
    # The caller must supply report_body, not the full report.
    if re.search(r"^## Sources\s*$", body, flags=re.MULTILINE):
        raise ValueError(
            "Supply the report body without its Sources section."
        )

    # Include only sources referenced in this report.
    # Unknown IDs must not receive invented source links.
    cited = citation_ids(body)
    known = {source["id"] for source in sources}
    unknown = cited - known

    if unknown:
        raise ValueError(
            "Unknown source IDs: " + ", ".join(sorted(unknown))
        )

    references = [
        source for source in sources if source["id"] in cited
    ]

    # Try readable body sizes, largest first.
    # Never truncate the text or shrink below nine points.
    for font_size in (10, 9.5, 9):
        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=30,
            bottomMargin=30,
            title=title,
            author="Amira Lions",
        )

        # Styles control appearance without changing the report wording.
        title_style = ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=colors.HexColor("#163A45"),
            spaceAfter=5,
        )

        note_style = ParagraphStyle(
            "ReviewNote",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=6,
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=font_size + 1,
            leading=font_size + 3,
            textColor=colors.HexColor("#163A45"),
            spaceBefore=5,
            spaceAfter=2,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            fontName="Helvetica",
            fontSize=font_size,
            leading=font_size + 2,
            spaceAfter=4,
        )

        source_style = ParagraphStyle(
            "SourceLink",
            fontName="Helvetica",
            fontSize=8,
            leading=9.5,
            spaceAfter=2,
            splitLongWords=True,
        )

        # A story is ReportLab's ordered list of layout elements.
        # Rebuild it on each attempt because build() consumes elements.
        story = [
            Paragraph(plain_text(title), title_style),
            Paragraph(plain_text(review_status), note_style),
        ]

        # Blank lines separate paragraphs in the generated Markdown.
        # Preserve single line breaks for lists and discovery questions.
        for block in re.split(r"\n\s*\n", body.strip()):
            lines = block.strip().splitlines()

            if lines[0].startswith("## "):
                story.append(
                    Paragraph(
                        plain_text(lines[0][3:].strip()),
                        heading_style,
                    )
                )
                lines = lines[1:]

            if lines:
                paragraph_text = "<br/>".join(
                    plain_text(line.strip()) for line in lines
                )
                story.append(Paragraph(paragraph_text, body_style))

        # Show full URLs so sources remain identifiable when printed.
        # Make them clickable when the PDF is viewed electronically.
        if references:
            story.append(Spacer(1, 3))
            story.append(Paragraph("Sources", heading_style))

            for source in references:
                url = source["url"]

                # Only ordinary web links belong in this source list.
                if not url.startswith(("https://", "http://")):
                    raise ValueError("A source has an unsupported URL.")

                label = plain_text(f"[{source['id']}] {url}")
                safe_url = escape(url, quote=True)

                story.append(
                    Paragraph(
                        f'<link href="{safe_url}" color="#155A80">'
                        f"{label}</link>",
                        source_style,
                    )
                )

        try:
            document.build(story)
        except LayoutError:
            # Try the next permitted font size if layout fails.
            continue

        pdf_bytes = buffer.getvalue()

        # Verify the actual PDF rather than assuming it fits.
        if len(PdfReader(BytesIO(pdf_bytes)).pages) == 1:
            return pdf_bytes

    # Do not silently cut evidence or return a multi-page report.
    raise ValueError(
        "The complete report does not fit on one page at a readable "
        "size. Shorten the body or reduce unnecessary cited sources."
    )


# END OF FILE