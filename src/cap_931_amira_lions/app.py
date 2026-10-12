import streamlit as st
from urllib.parse import urlparse
# Display the application heading.
st.title("FreedomFlyer Sales Assistant")
st.subheader("Account Research Inputs")
# Collect sales research inputs, prefilled with the FreedomFlyer scenario.
# Submit the fields together when the user clicks Review Inputs.
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
    # Accept one competitor URL per line.
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

    submitted = st.form_submit_button("Review Inputs")
# Validate submitted inputs before displaying the review.
if submitted:
    # Check that every required field contains text.
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

    # Define a reusable URL-format check.
    def valid_url(value):
        try:
            parsed = urlparse(value.strip())
            return (
                parsed.scheme in ("http", "https")
                and bool(parsed.hostname)
                and not any(character.isspace() for character in value)
            )
        except ValueError:
            return False

    if company_url.strip() and not valid_url(company_url):
        errors.append(
            "Prospect company URL must be a valid HTTP or HTTPS URL."
        )

    # Remove empty lines and spaces around competitor URLs.
    competitor_list = [
        line.strip()
        for line in competitor_urls.splitlines()
        if line.strip()
    ]

    for number, url in enumerate(competitor_list, start=1):
        if not valid_url(url):
            errors.append(
                f"Competitor URL {number} needs a valid HTTP or HTTPS URL."
            )

    # Show errors, or display the accepted inputs.
    if errors:
        for message in errors:
            st.error(message)
    else:
        st.success("Input checks passed.")
        st.subheader("Review Your Inputs")

        st.write({
            "Product name": product_name.strip(),
            "Prospect company URL": company_url.strip(),
            "Product category": product_category.strip(),
            "Competitor URLs": competitor_list,
            "Value proposition": value_proposition.strip(),
            "Target customer": target_customer.strip(),
        })