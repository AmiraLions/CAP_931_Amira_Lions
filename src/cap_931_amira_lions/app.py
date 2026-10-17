"""
FreedomFlyer sales research interface.

Workflow:
1. Collect and validate the user's inputs.
2. Retrieve public HTML pages without calling GPT.
3. Generate research findings and a brief when explicitly requested.
"""

# Streamlit creates the browser interface.
import streamlit as st

# Build downloadable experiment records without another model request.
import json

# urlparse helps check the format of website addresses.
from urllib.parse import urlparse

# OpenAIError lets us handle API failures without displaying
# the full technical exception in the browser.
from openai import OpenAIError

# Import our own retrieval and two-step model functions.
from cap_931_amira_lions.web_research import fetch_page
from cap_931_amira_lions.llm_client import generate_brief

# Read uploaded PDFs and TXT files locally before any model request.
from cap_931_amira_lions.document_reader import read_document, MAX_FILE_BYTES


def valid_url(value):
    """Check basic URL format, not website availability."""
    try:
        parsed = urlparse(value.strip())
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and not any(character.isspace() for character in value)
        )
    except ValueError:
        return False


# Streamlit reruns this file when the user interacts with widgets.
# Session state keeps evidence and results across those reruns.
# These values belong to the current browser session.
for key, initial_value in {
    "account_inputs": None,
    "retrieved_pages": [],
    "brief_result": None,
    "product_document": None,
    "include_product_document": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = initial_value


st.title("FreedomFlyer Sales Assistant")
st.subheader("Account Research Inputs")

# A form submits all its field values together.
# Editing fields alone does not download pages or call GPT.
with st.form("sales_inputs"):
    product_name = st.text_input(
        "Product name",
        value="FreedomFlyer",
    )

    company_url = st.text_input(
        "Prospect company URL",
        value="https://www.sunshinestatervs.com/",
    )

    product_category = st.text_input(
        "Product category",
        value="Electric luxury Class B motorhomes",
    )

    # Each line becomes a separate competitor source.
    competitor_urls = st.text_area(
        "Competitor URLs - one per line",
        value="\n".join([
            "https://coachmenrv.com/nova",
            "https://coachmenrv.com/pixel",
            "https://coachmenrv.com/beyond",
            "https://coachmenrv.com/galleria",
            "https://www.winnebago.com/models/solis-series/solis",
            "https://www.winnebago.com/models/solis-series/solis-pocket",
            "https://www.winnebago.com/models/motorhomes/camper-van/travato",
            "https://www.midwestautomotivedesigns.com/brand/patriot",
            "https://www.midwestautomotivedesigns.com/brand/mercedes-luxe-cruiser",
            "https://www.noovolife.com/noovo-lite/",
            "https://www.noovolife.com/noovo-next/",
            "https://roadtrek.com/models/ss-agile/",
            "https://tiffinadventure.com/2027-gh1-se/",
        ]),
        height=200,
    )

    value_proposition = st.text_area(
        "Value proposition",
        value=(
            "FreedomFlyer offers electric luxury Class B motorhomes "
            "with zero tailpipe emissions and an expandable solar "
            "system designed to support beautiful advantures!"
        ),
    )

    target_customer = st.text_input(
        "Target customer",
        value="Nick Schmidt, General Manager/Owner",
    )

    # Additional prospect pages provide evidence that a homepage
    # may lack, such as staff roles, new inventory, or company news.
    # This optional field does not replace the prospect's main URL.
    additional_urls = st.text_area(
        "Additional prospect source URLs - optional, one per line",
        # Save these as defaults so restarting does not lose inventory pages.
        # They remain editable for other prospective accounts.
        value="\n".join([
            "https://www.sunshinestatervs.com/--xstaff",
            "https://www.sunshinestatervs.com/--inventory?condition=new",
            "https://www.sunshinestatervs.com/--inventory?condition=new&pg=2",
            "https://www.sunshinestatervs.com/--inventory?condition=new&pg=3",
            "https://www.sunshinestatervs.com/--inventory?condition=new&pg=4",
            "https://www.sunshinestatervs.com/--inventory?condition=new&pg=5",
        ]),
    )

    # Uploading or reviewing a file does not contact OpenAI.
    # The file stays in session memory; we do not save its bytes to disk.
    # The reader also enforces a 5 MB limit and a 30-page PDF limit.
    product_upload = st.file_uploader(
        "Product overview - optional PDF or TXT",
        type=["pdf", "txt"],
        help="Text-based PDF or UTF-8 TXT, up to 5 MB. Scans need OCR.",
    )

    # The user can preview locally without agreeing to send the text.
    # Explicitly identify the external service and the later action.
    include_document = st.checkbox(
        "Include the extracted product text in OpenAI requests "
        "when I click Generate Sales Brief",
        value=False,
    )
    st.caption(
        "Upload only material you are authorized to use. "
        "Document text is user-provided context, not verified web evidence. "
        "Experiment downloads will contain it if you include it."
    )

    submitted = st.form_submit_button("Review Inputs")


if submitted:
    # Clear earlier evidence and reports whenever a new submission
    # arrives. This prevents reuse with changed or invalid inputs.
    st.session_state.account_inputs = None
    st.session_state.retrieved_pages = []
    st.session_state.brief_result = None
    # Clear old document text on every new form submission.
    # Removing a file must not leave its earlier contents in a new report.
    st.session_state.product_document = None
    st.session_state.include_product_document = False

    required_fields = {
        "Product name": product_name,
        "Prospect company URL": company_url,
        "Product category": product_category,
        "Competitor URLs": competitor_urls,
        "Value proposition": value_proposition,
        "Target customer": target_customer,
    }

    errors = []
    for label, value in required_fields.items():
        if not value.strip():
            errors.append(f"Please enter {label}.")

    # Ignore blank lines and remove surrounding spaces.
    competitor_list = [
        line.strip()
        for line in competitor_urls.splitlines()
        if line.strip()
    ]
    additional_list = [
        line.strip()
        for line in additional_urls.splitlines()
        if line.strip()
    ]

    if company_url.strip() and not valid_url(company_url):
        errors.append(
            "Prospect company URL must be a valid HTTP or HTTPS URL."
        )

    for number, url in enumerate(competitor_list, start=1):
        if not valid_url(url):
            errors.append(
                f"Competitor URL {number} needs a valid HTTP or HTTPS URL."
            )

    for number, url in enumerate(additional_list, start=1):
        if not valid_url(url):
            errors.append(
                f"Additional source URL {number} needs a valid "
                "HTTP or HTTPS URL."
            )

    # Read optional document contents only when the form is submitted.
    # Check upload size before copying its bytes into the parser.
    document = None
    if product_upload is not None:
        if product_upload.size > MAX_FILE_BYTES:
            errors.append("Please upload a file no larger than 5 MB.")
        else:
            document = read_document(
                product_upload.name, product_upload.getvalue()
            )
            if document["error"]:
                errors.append(document["error"])

    if errors:
        for message in errors:
            st.error(message)
    else:
        # Store extracted text and the user's sending preference separately
        # from the web-source list. Do not assign the document a web ID.
        st.session_state.product_document = document
        st.session_state.include_product_document = bool(
            document and include_document
        )

        # Store the validated inputs for retrieval and report generation.
        st.session_state.account_inputs = {
            "Product name": product_name.strip(),
            "Prospect company URL": company_url.strip(),
            "Product category": product_category.strip(),
            "Competitor URLs": competitor_list,
            "Value proposition": value_proposition.strip(),
            "Target customer": target_customer.strip(),
            "Additional prospect URLs": additional_list,
        }


# Display the last successfully submitted inputs.
# Unsaved form edits do not change this stored research scenario.
if st.session_state.account_inputs is not None:
    account = st.session_state.account_inputs

    st.success("Input checks passed.")
    st.subheader("Review Your Inputs")
    st.write(account)
    st.caption(
        "After editing the form, click Review Inputs again to apply changes."
    )

    # Show the last submitted document, not unsaved form edits.
    # Plain text avoids interpreting document contents as Markdown.
    document = st.session_state.product_document
    if document is not None:
        st.subheader("Product Document Preview")
        st.write("Filename:", document["filename"])
        st.write("Characters extracted:", len(document["text"]))
        for warning in document["warnings"]:
            st.warning(warning)
        with st.expander("View extracted product text"):
            st.text(document["text"])
        if st.session_state.include_product_document:
            st.info("This text will be sent to OpenAI when you generate a brief.")
        else:
            st.info("Preview only: this document will not be sent to OpenAI.")

    # Retrieval is separate from form submission and GPT generation.
    # This button downloads websites but does not spend API credit.
    if st.button("Retrieve Web Evidence"):
        st.session_state.retrieved_pages = []
        st.session_state.brief_result = None

        # Combine prospect and competitor sources.
        # dict.fromkeys removes duplicate URLs while preserving order.
        urls = list(dict.fromkeys(
            [account["Prospect company URL"]]
            + account["Additional prospect URLs"]
            + account["Competitor URLs"]
        ))

        # Download pages one at a time and show which one is in progress.
        # Failed pages remain in the results so we can report gaps.
        progress = st.progress(0.0)
        for number, url in enumerate(urls, start=1):
            with st.spinner(
                f"Retrieving source {number} of {len(urls)}: {url}"
            ):
                page = fetch_page(url)
                st.session_state.retrieved_pages.append(page)

            progress.progress(number / len(urls))

        progress.empty()


# Keep evidence visible across reruns, including the GPT button click.
if st.session_state.retrieved_pages:
    pages = st.session_state.retrieved_pages
    usable_pages = [
        page
        for page in pages
        if not page["error"] and page["text"]
    ]

    st.subheader("Retrieved Web Evidence")
    st.write(
        f"{len(usable_pages)} of {len(pages)} sources returned readable text."
    )

    for number, page in enumerate(pages, start=1):
        # The number here identifies retrieval order.
        # Citation IDs are assigned separately by llm_client.py
        # to the usable sources only.
        with st.expander(
            f"Source {number}: {page['title'] or page['url']}"
        ):
            st.write("Source URL:", page["url"])
            if page["error"]:
                st.warning(page["error"])
            else:
                st.write("Characters extracted:", len(page["text"]))
                st.text(page["text"])

    if usable_pages:
        st.caption(
            "Generate Sales Brief sends two paid requests to OpenAI "
            "using the submitted inputs and readable evidence. "
            "Review factual claims and citations before using the draft."
        )

        # A GPT request happens only when this button is clicked.
        # Expanding evidence or downloading a result does not call GPT.
        if st.button("Generate Sales Brief"):
            st.session_state.brief_result = None

            try:
                with st.spinner("Researching evidence and drafting brief..."):
                    result = generate_brief(
                        st.session_state.account_inputs,
                        pages,
                        # Pass only successfully extracted text that the
                        # user explicitly chose to include in generation.
                        product_document=(
                            st.session_state.product_document
                            if st.session_state.include_product_document
                            else None
                        ),
                    )
                # Preserve failed-page information too, so the experiment
                # describes retrieval coverage rather than hiding failures.
                result["retrieval_summary"] = {
                    "attempted": len(pages),
                    "readable": len(usable_pages),
                    "failures": [
                        {"url": p["url"], "error": p["error"]}
                        for p in pages if p["error"]
                    ],
                }
                st.session_state.brief_result = result

            except OpenAIError:
                # Avoid exposing raw API exception details.
                st.error(
                    "The OpenAI request failed. Check API access, "
                    "available credit, and your connection before retrying. "
                    "A completed first step may already have used credit."
                )
            except ValueError as error:
                # Our module raises these messages for missing settings,
                # missing evidence, or incomplete model responses.
                st.error(str(error))
    else:
        st.warning(
            "No readable sources are available. Add or correct source "
            "URLs, submit the form again, and retry retrieval."
        )


# Display a saved result without generating it again.
if st.session_state.brief_result is not None:
    result = st.session_state.brief_result

    st.subheader("Draft Sales Brief")
    st.markdown(result["report"])

    # These checks run locally and incur no API charge.
    # Passing them does not mean the claims are factually correct.
    checks = result.get("checks")
    if checks:
        st.write("Body word count:", checks["word_count"])
        if checks["mechanical_checks_passed"]:
            st.success("Mechanical checks passed. Factual review is still required.")
        else:
            for warning in checks["warnings"]:
                st.warning(warning)
        with st.expander("Review automatic checks"):
            st.write(checks)
    else:
        st.info("This older result has no automatic checks. Generate a new draft when ready.")

    # Show the underlying research and source records for review.
    with st.expander("Review research findings"):
        st.markdown(result["research"])

    with st.expander("Review source records"):
        st.write(result["sources"])

    with st.expander("Review model and token usage"):
        st.write(result["usage"])

    # Provide a downloadable Markdown draft.
    # A formatted one-page document will be added later.
    st.download_button(
        "Download Draft Brief",
        data=result["report"],
        file_name="FreedomFlyer_sales_brief.md",
        mime="text/markdown",
    )

    # Combine the draft, findings, usage, and checks in one human-readable
    # experiment download. Editing this number does not call the model.
    experiment_number = st.number_input(
        "Experiment number for downloads", min_value=1, value=4, step=1
    )
    record = (
        f"# Experiment {experiment_number} - Sales Brief\n\n"
        f"Generated (UTC): {result.get('generated_at_utc', 'not recorded')}\n\n"
        f"Prompt revision: {result.get('prompt_revision', 'not recorded')}\n\n"
        "Status: Generated draft; human factual review required.\n\n"
        "## Generated Brief\n\n" + result["report"]
        + "\n\n## Research Findings\n\n" + result["research"]
        + "\n\n## Model and Token Usage\n\n```json\n"
        + json.dumps(result["usage"], indent=2) + "\n```"
        + "\n\n## Automatic Checks\n\n```json\n"
        + json.dumps(result.get("checks", {}), indent=2) + "\n```"
        + "\n\n## Retrieval Summary\n\n```json\n"
        + json.dumps(result.get("retrieval_summary", {}), indent=2)
        + "\n```\n\n## Human Review Notes\n\nPending review.\n"
    )
    st.download_button(
        "Download Experiment Record",
        data=record,
        file_name=f"experiment_{int(experiment_number):02d}_sales_brief.md",
        mime="text/markdown",
    )

    # JSON also preserves inputs, exact prompts, and retrieved text.
    # This supports later auditing without downloading the same pages.
    # Inspect for private form inputs before sharing this snapshot.
    st.download_button(
        "Download Evidence and Experiment Snapshot",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name=f"experiment_{int(experiment_number):02d}_snapshot.json",
        mime="application/json",
    )
# PDF EXPORT
# This section formats the existing result without contacting OpenAI.
from cap_931_amira_lions.report_generator import build_report_pdf
import hashlib


# Show PDF controls only when this browser session has a generated brief.
if st.session_state.brief_result is not None:
    pdf_result = st.session_state.brief_result

    st.subheader("Prepare One-Page PDF")
    st.caption(
        "Review factual claims and citations before exporting. "
        "Formatting a PDF does not verify its accuracy."
    )

    # Use the body without the Sources section.
    # The PDF generator builds references from the source records.
    original_body = pdf_result["report_body"]

    # Give each generated result its own editor.
    # This prevents edits from an earlier result appearing in a new one.
    result_id = hashlib.sha256(
        (
            pdf_result.get("generated_at_utc", "")
            + original_body
        ).encode("utf-8")
    ).hexdigest()

    edited_body = st.text_area(
        "Brief body for PDF - editable",
        value=original_body,
        height=350,
        key=f"pdf_editor_{result_id}",
    )

    # Fingerprint the exact text and sources used for this PDF.
    # If either changes, hide any PDF prepared from older contents.
    pdf_signature = hashlib.sha256(
        (
            edited_body
            + json.dumps(pdf_result["sources"], sort_keys=True)
        ).encode("utf-8")
    ).hexdigest()

    if st.button("Prepare PDF"):
        # Discard an older prepared file before attempting a new one.
        st.session_state.prepared_pdf = None

        # Describe editing honestly without claiming factual approval.
        if edited_body != original_body:
            review_status = (
                "AI draft edited in app; human factual review required."
            )
        else:
            review_status = (
                "AI-generated draft; human factual review required."
            )

        try:
            pdf_bytes = build_report_pdf(
                body=edited_body,
                sources=pdf_result["sources"],
                review_status=review_status,
            )

            # Store bytes so downloading does not regenerate the report.
            st.session_state.prepared_pdf = {
                "signature": pdf_signature,
                "bytes": pdf_bytes,
            }

            st.success("One-page PDF prepared.")

        except ValueError as error:
            # For example, the content may not fit on one page,
            # or an edited citation may reference an unknown source.
            st.error(str(error))

    prepared = st.session_state.get("prepared_pdf")

    # Offer only a PDF matching the current editor text and sources.
    if prepared and prepared["signature"] == pdf_signature:
        st.download_button(
            "Download One-Page PDF",
            data=prepared["bytes"],
            file_name="FreedomFlyer_sales_brief.pdf",
            mime="application/pdf",
        )
# LOAD A SAVED EXPERIMENT
# This section is outside the form and appears even without a new brief.
# Loading saved JSON does not call GPT or retrieve websites.

st.subheader("Open a Saved Experiment")

saved_experiment = st.file_uploader(
    "Upload an experiment snapshot JSON",
    type=["json"],
    key="saved_experiment_upload",
)

if saved_experiment is not None:
    if st.button("Load Saved Experiment"):
        try:
            # Check size before reading the uploaded file.
            if saved_experiment.size > 5 * 1024 * 1024:
                raise ValueError("The snapshot exceeds 5 MB.")

            # Read JSON as data, not executable Python.
            snapshot = json.loads(
                saved_experiment.getvalue().decode("utf-8-sig")
            )

            if not isinstance(snapshot, dict):
                raise ValueError("Invalid snapshot structure.")

            # Confirm the fields needed to display the saved result.
            for field in ("report_body", "report", "research"):
                if not isinstance(snapshot.get(field), str):
                    raise ValueError("Missing report text.")

            if not isinstance(snapshot.get("sources"), list):
                raise ValueError("Missing source list.")

            if not isinstance(snapshot.get("usage"), list):
                raise ValueError("Missing usage list.")

            for source in snapshot["sources"]:
                if not isinstance(source, dict):
                    raise ValueError("Invalid source record.")

                for field in ("id", "title", "url"):
                    if not isinstance(source.get(field), str):
                        raise ValueError("Incomplete source record.")

            # Recalculate checks using the current checker.
            from cap_931_amira_lions.llm_client import check_report

            snapshot["checks"] = check_report(
                snapshot["report_body"], snapshot["sources"]
            )

            # Store the result and remove any previously prepared PDF.
            st.session_state.brief_result = snapshot
            st.session_state.prepared_pdf = None

            # Refresh the app to display the loaded report above.
            st.rerun()

        except (ValueError, UnicodeDecodeError):
            st.error(
                "Could not load this file. Use a JSON experiment "
                "snapshot downloaded from this app."
            )

# END OF SAVED EXPERIMENT LOADER