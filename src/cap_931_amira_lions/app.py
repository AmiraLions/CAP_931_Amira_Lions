"""
FreedomFlyer sales research interface.

Workflow:
1. Collect and validate the user's inputs.
2. Retrieve public HTML pages without calling GPT.
3. Generate research findings and a brief when explicitly requested.
"""

# Streamlit creates the browser interface.
import streamlit as st

# urlparse helps check the format of website addresses.
from urllib.parse import urlparse

# OpenAIError lets us handle API failures without displaying
# the full technical exception in the browser.
from openai import OpenAIError

# Import our own retrieval and two-step model functions.
from cap_931_amira_lions.web_research import fetch_page
from cap_931_amira_lions.llm_client import generate_brief


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
        "Competitor URLs — one per line",
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
        "Additional prospect source URLs — optional, one per line",
        value="https://www.sunshinestatervs.com/--xstaff",
    )

    submitted = st.form_submit_button("Review Inputs")


if submitted:
    # Clear earlier evidence and reports whenever a new submission
    # arrives. This prevents reuse with changed or invalid inputs.
    st.session_state.account_inputs = None
    st.session_state.retrieved_pages = []
    st.session_state.brief_result = None

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

    if errors:
        for message in errors:
            st.error(message)
    else:
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
                        usable_pages,
                    )
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