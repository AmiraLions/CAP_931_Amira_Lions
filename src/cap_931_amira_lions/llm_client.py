"""
Connect the sales assistant to OpenAI.

This module runs two model steps:
1. Extract research findings from source text.
2. Draft a sales brief from those findings.

Requests happen only when generate_brief() is called.
"""

# json converts Python dictionaries and lists into text for the model.
import json

# os lets us read settings loaded into the process environment.
import os

# Path helps us locate .env relative to this file.
from pathlib import Path

# Load local environment settings and the OpenAI API client.
from dotenv import load_dotenv
from openai import OpenAI

# Import the instructions stored in our separate prompts module.
from cap_931_amira_lions.prompts import (
    SALES_ASSISTANT_INSTRUCTIONS,
    RESEARCH_INSTRUCTIONS,
    REPORT_INSTRUCTIONS,
)


def generate_brief(account_inputs, sources):
    """
    Generate research findings and a sales brief.

    account_inputs: dictionary of the validated form entries.
    sources: list of successfully retrieved page dictionaries.

    API errors are allowed to reach the calling code.
    The Streamlit interface will handle and display those errors.
    """

    # This file is inside src/package_name/.
    # Moving up two directory levels reaches the project root.
    # An explicit path avoids depending on the terminal's folder.
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    # Confirm a key is available without printing it.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from local settings.")

    # Use the configured model, or our chosen default if not configured.
    model = os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"

    # Ignore failed or empty retrievals.
    # They cannot provide evidence for factual claims.
    usable_sources = [
        source
        for source in sources
        if not source.get("error") and source.get("text")
    ]

    if not usable_sources:
        raise ValueError("No readable sources are available for research.")

    # Assign each usable source an ID for citations.
    # Keep the text with its title and URL so evidence stays attributable.
    source_records = []
    for number, source in enumerate(usable_sources, start=1):
        source_records.append({
            "id": f"S{number}",
            "url": source["url"],
            "title": source.get("title", ""),
            "text": source["text"],
        })

    # Limit waiting and automatic retries.
    # A failed request will be reported to the calling interface.
    client = OpenAI(
        api_key=api_key,
        timeout=60.0,
        max_retries=0,
    )

    # Convert the inputs and evidence into a JSON string.
    # JSON provides a consistent structure; it does not itself
    # prevent malicious instructions embedded in source text.
    research_input = json.dumps(
        {
            "account_inputs": account_inputs,
            "sources": source_records,
        },
        ensure_ascii=False,
    )

    # FIRST PAID REQUEST: extract evidence from the supplied sources.
    # Shared boundaries and task instructions are sent separately
    # from the input data.
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

    # Stop if the first step did not produce usable findings.
    if (
        research_response.status != "completed"
        or not research_response.output_text.strip()
    ):
        raise ValueError(
            "The research step did not complete with usable findings."
        )

    # Prepare a compact source list for the second step.
    # The supporting excerpts are already in the research findings.
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

    # SECOND PAID REQUEST: turn the first step's findings into a brief.
    # Passing one step's result to the next is prompt chaining.
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

    # Record usage separately for each model step.
    # These figures help document experiments and estimate cost.
    usage = []
    for step, response in [
        ("research", research_response),
        ("report", report_response),
    ]:
        usage.append({
            "step": step,
            "model": response.model,
            "input_tokens": (
                response.usage.input_tokens if response.usage else None
            ),
            "output_tokens": (
                response.usage.output_tokens if response.usage else None
            ),
        })

    # Return the outputs to the interface.
    # The draft still needs review for factual and citation accuracy.
    return {
        "research": research_response.output_text,
        "report": report_response.output_text,
        "sources": source_links,
        "usage": usage,
    }