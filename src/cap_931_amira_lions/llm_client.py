"""
Connect the sales assistant to OpenAI.

Step 1 extracts research findings from retrieved evidence.
Step 2 drafts a sales brief from those findings.

Importing this module does not make an API request.
Requests happen only when generate_brief() is called.
"""

# Convert dictionaries and lists into text for API inputs and downloads.
import json

# Read settings such as OPENAI_API_KEY from the environment.
import os

# Find headings, citation markers, and words in the generated report.
import re

# Record when an experiment was generated, using UTC.
from datetime import datetime, timezone

# Locate the project's .env file relative to this module.
from pathlib import Path

# Load local settings and communicate with OpenAI.
from dotenv import load_dotenv
from openai import OpenAI

# Import the instructions defined in our separate prompts file.
from cap_931_amira_lions.prompts import (
    SALES_ASSISTANT_INSTRUCTIONS,
    RESEARCH_INSTRUCTIONS,
    REPORT_INSTRUCTIONS,
)


# These headings match the report structure requested in prompts.py.
REQUIRED_HEADINGS = [
    "Prospect and target contact",
    "Company strategy",
    "Competitors and positioning",
    "Leadership and relevant reports",
    "Proposed conversation angle and two discovery questions",
    "Evidence gaps",
]


def citation_ids(body):
    """Read individual, grouped, and ranged source IDs without API calls."""
    # Keep formatting warnings separate from ID extraction.
    # Even a badly formatted group must not silently lose references.
    found = set()
    for marker in re.findall(r"\[S[^\]\n]*\]", body):
        # Read explicit IDs first, including unknown range endpoints.
        found.update(re.findall(r"S\d+", marker))

        # Accept ranges such as S3-S7, S3–S7, or S3-7.
        # Cap expansion to avoid allocating huge ranges from bad output.
        for match in re.finditer(
            r"S(\d+)\s*[-–—]\s*S?(\d+)", marker
        ):
            start, end = map(int, match.groups())
            found.update((f"S{start}", f"S{end}"))
            if 0 < start <= end and end - start <= 100:
                found.update(f"S{n}" for n in range(start, end + 1))
    return found


def check_report(body, source_links):
    """
    Check report structure locally without making an API request.

    These checks identify formatting and citation-ID problems.
    They cannot prove that a source supports a factual claim.
    """

    # Remove headings and citation markers before counting body words.
    # Hyphenated words count as one under this counting method.
    prose = re.sub(
        r"^#{1,6} .*?$", "", body, flags=re.MULTILINE
    )
    prose = re.sub(r"\[S[^\]\n]*\]", "", prose)
    word_count = len(
        re.findall(r"\b\w+(?:[-'’]\w+)*\b", prose)
    )

    # Compare cited IDs with the IDs assigned to retrieved sources.
    known = {source["id"] for source in source_links}
    # Extract all referenced IDs even when formatting needs correction.
    # Unknown IDs remain warnings and never receive invented URLs.
    cited = citation_ids(body)
    unknown = sorted(cited - known)

    # Require individual markers like [S1], not ranges or groups.
    markers = re.findall(r"\[S[^\]\n]*\]", body)
    malformed = [
        marker
        for marker in markers
        if not re.fullmatch(r"\[S\d+\]", marker)
    ]

    # Read second-level Markdown headings and check their order.
    headings = re.findall(
        r"^## (.+?)\s*$", body, flags=re.MULTILINE
    )
    missing = [
        heading
        for heading in REQUIRED_HEADINGS
        if heading not in headings
    ]

    # Look for exactly two numbered discovery questions.
    questions = re.findall(
        r"^\s*([12])\.\s+.+", body, flags=re.MULTILINE
    )

    # Collect issues without deleting the draft or paying for a retry.
    warnings = []

    if not 350 <= word_count <= 450:
        warnings.append(
            f"Body has {word_count} words; target is 350–450."
        )

    if missing:
        warnings.append(
            "Missing sections: " + "; ".join(missing)
        )

    if headings != REQUIRED_HEADINGS:
        warnings.append(
            "Section order or heading format differs from the template."
        )

    if unknown:
        warnings.append(
            "Unknown citation IDs: " + ", ".join(unknown)
        )

    if malformed:
        warnings.append(
            "Use separate citations like [S1] [S2], not ranges or groups."
        )

    if not cited:
        warnings.append("No source citations were found.")

    if questions != ["1", "2"]:
        warnings.append(
            "Expected two numbered discovery questions: 1. and 2."
        )

    # Check important brand wording when FreedomFlyer is mentioned.
    # These are presence checks, not a full review of sentence meaning.
    lower = body.lower()

    if "freedomflyer" in lower:
        if "fictional" not in lower:
            warnings.append(
                "FreedomFlyer's fictional status is not stated."
            )

        if "zero tailpipe emissions" not in lower:
            warnings.append(
                "The required zero tailpipe emissions phrase is missing."
            )

        if "advantures" not in lower:
            warnings.append(
                "Intentional brand wording advantures is missing."
            )

    # The application builds the source list from known records.
    if re.search(r"https?://", body):
        warnings.append(
            "Unexpected URL in body; use the application source list."
        )

    return {
        "word_count": word_count,
        "missing_sections": missing,
        "unknown_citation_ids": unknown,
        "cited_source_ids": sorted(
            cited, key=lambda item: int(item[1:])
        ),
        "warnings": warnings,
        "mechanical_checks_passed": not warnings,
        "factual_review_required": True,
    }


def generate_brief(account_inputs, sources):
    """
    Run two paid model requests and return the results.

    account_inputs contains the submitted, validated form values.
    sources contains retrieved page dictionaries.

    The calling Streamlit code handles API and validation errors.
    """

    # This module lives in project_root/src/package_name/.
    # parents[2] reaches the project root.
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    # Read the key without printing or including it in results.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing from local settings."
        )

    # Use the configured model, with our chosen model as the default.
    model = os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"

    # Failed or empty pages cannot supply evidence.
    usable_sources = [
        source
        for source in sources
        if not source.get("error") and source.get("text")
    ]

    if not usable_sources:
        raise ValueError(
            "No readable sources are available for research."
        )

    # Assign citation IDs to usable sources.
    # IDs depend on source order in this particular run.
    source_records = []

    for number, source in enumerate(usable_sources, start=1):
        source_records.append({
            "id": f"S{number}",
            "url": source["url"],
            "title": source.get("title", ""),
            "text": source["text"],
        })

    # Set a timeout and disable automatic request retries.
    # The user controls whether to try again after a failure.
    client = OpenAI(
        api_key=api_key,
        timeout=60.0,
        max_retries=0,
    )

    # Package the submitted scenario and source text for research.
    # JSON organizes data but does not prevent prompt injection.
    research_input = json.dumps(
        {
            "account_inputs": account_inputs,
            "sources": source_records,
        },
        ensure_ascii=False,
    )

    # FIRST PAID REQUEST: extract supported research findings.
    research_response = client.responses.create(
        model=model,
        instructions=(
            SALES_ASSISTANT_INSTRUCTIONS
            + "\n\n"
            + RESEARCH_INSTRUCTIONS
        ),
        input=research_input,
        max_output_tokens=2500,
    )

    # Do not continue if research is incomplete or empty.
    if (
        research_response.status != "completed"
        or not research_response.output_text.strip()
    ):
        raise ValueError(
            "The research step did not complete with usable findings."
        )

    # Prepare source references without repeating all downloaded text
    # in the second request. Findings should retain supporting excerpts.
    source_links = [
        {
            "id": source["id"],
            "url": source["url"],
            "title": source["title"],
        }
        for source in source_records
    ]

    report_input = json.dumps(
        {
            "account_inputs": account_inputs,
            "research_findings": research_response.output_text,
            "sources": source_links,
        },
        ensure_ascii=False,
    )

    # SECOND PAID REQUEST: draft the brief using the research output.
    # Passing the first result into this step is prompt chaining.
    report_response = client.responses.create(
        model=model,
        instructions=(
            SALES_ASSISTANT_INSTRUCTIONS
            + "\n\n"
            + REPORT_INSTRUCTIONS
        ),
        input=report_input,
        max_output_tokens=1800,
    )

    if (
        report_response.status != "completed"
        or not report_response.output_text.strip()
    ):
        raise ValueError(
            "The report step did not complete with a usable brief."
        )

    # Preserve actual model identifiers and token usage for both steps.
    usage = []

    for step, response in [
        ("research", research_response),
        ("report", report_response),
    ]:
        usage.append({
            "step": step,
            "model": response.model,
            "input_tokens": (
                response.usage.input_tokens
                if response.usage else None
            ),
            "output_tokens": (
                response.usage.output_tokens
                if response.usage else None
            ),
        })

    # Run free local checks before appending the source list.
    # A warning does not trigger another paid model request.
    body = report_response.output_text.strip()
    checks = check_report(body, source_links)

    # Build references from known source records, not model-written URLs.
    # Unknown citation IDs remain flagged in the automatic checks.
    cited = set(checks["cited_source_ids"])
    references = [
        f"[{source['id']}] {source['title']} — {source['url']}"
        for source in source_links
        if source["id"] in cited
    ]

    report = (
        body
        + "\n\n## Sources\n\n"
        + "\n\n".join(references)
    )

    # Return the draft and audit information to Streamlit.
    # No API key is included.
    # The snapshot includes submitted inputs and public source text;
    # review it before sharing if future inputs contain private data.
    return {
        "research": research_response.output_text,
        "report": report,
        "report_body": body,
        "checks": checks,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_revision": "3",
        "code_revision": "citation-and-page-quality-fix-1",
        "account_inputs": account_inputs,
        "source_snapshot": source_records,
        "prompt_snapshot": {
            "shared": SALES_ASSISTANT_INSTRUCTIONS,
            "research": RESEARCH_INSTRUCTIONS,
            "report": REPORT_INSTRUCTIONS,
        },
        "sources": source_links,
        "usage": usage,
    }

# END OF FILE