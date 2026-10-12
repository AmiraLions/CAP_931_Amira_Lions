# CAP 931 — FreedomFlyer Sales Assistant

Author: Amira Lions

## Project Purpose

Build a Python and Streamli```

Open the Local URL displayed in the terminal.
Press Ctrl+C in the terminal to stop the app.

## Manual Validation Tests

Performed October 11, 2026. Results observed and reported by the author.

| Test | Expected behavior | Result |
|---|---|---|
| Blank product name | Required-field error | Passed |
| Prospect URL entered as hello | URL-format error | Passed |
| hello added as competitor entry 14 | Error identifying entry 14 | Passed |
| Original valid values restored | Success message and reviewed inputs | Passed |

Invalid submissions did not display the input review.

## Remaining Work

- Optional product-document upload and text extraction.
- LLM access, model selection, and justification.
- Web retrieval and retrieval error handling.
- Prompt chaining and sales-research constraints.
- Sourced one-page report using the Per Scholas template.
- Model or prompt experiments and output evaluation.
- Optional enhancement implementation.
- Git/GitHub checkpoint.
- Complete setup instructions and technical documentation.
- Challenges and solutions.
- Production deployment plan covering scalability, security,
  and maintenance.

## Time Management

- Product and account planning: approximately 3 hours.
  Defined FreedomFlyer, selected Sunshine State RVs and the target
  contact, and identified competitor brands and model URLs.
  This established the sales scenario and research inputs.
- Other work-session durations: not yet recorded.t sales assistant that researches a
prospective account and generates a sourced, one-page sales brief.

FreedomFlyer is a fictional electric luxury Class B motorhome brand.
Its proposed features are design targets, not verified production
specifications.

## Sales Scenario

- Product: FreedomFlyer
- Category: Electric luxury Class B motorhomes
- Prospect: Sunshine State RVs
- Website: https://www.sunshinestatervs.com/
- Target contact: Nick Schmidt, General Manager/Owner
- Leadership source: https://www.sunshinestatervs.com/--xstaff
- Competitor brands: Coachmen RV, Winnebago, Midwest Automotive
  Designs, Noovo, Roadtrek, and Tiffin Motorhomes
- Value proposition: FreedomFlyer offers electric luxury Class B
  motorhomes with zero tailpipe emissions and an expandable solar
  system designed to support beautiful advantures!

“Advantures” is intentional brand wording.

## Current Implementation

- Packaged Python project managed with uv.
- Streamlit interface in src/cap_931_amira_lions/app.py.
- Six editable research inputs with prefilled example values.
- Required-field checks that reject blank or whitespace-only entries.
- Basic HTTP/HTTPS URL-format checks.
- Error messages for invalid inputs.
- Reviewed inputs displayed when validation passes.

URL validation checks basic format. It does not confirm website
availability. LLM integration and web retrieval are not implemented yet.

## Run the Current App

From the project root:

```powershell
uv run streamlit run src/cap_931_amira_lions/app.py
## API Connection Test

On October 12, 2026, api_check.py successfully connected to OpenAI.

- Response: API connection successful
- Model returned: gpt-4.1-mini-2025-04-14
- Input tokens: 14
- Output tokens: 4
- Total tokens: 18

The API key is stored locally in .env, which Git ignores.
## Challenges and Solutions

### Website whitespace caused a false-negative name check

When I tested web_research.py against the dealership's staff page,
the download succeeded, but an exact search for "Nick Schmidt"
returned False.

I inspected the extracted text and found that the page contained
"Nick  Schmidt" with two spaces, plus separate lines for his name.

For the verification check, I normalized whitespace using:

    normalized = " ".join(page["text"].split()).lower()

split() separates text at whitespace, and join() reconnects the
words with single spaces. lower() makes the comparison insensitive
to capitalization.

After this change, the check found both Nick Schmidt and
"General Manager/Owner". The retrieval error was None.

This taught me that a failed text match does not necessarily mean
the source information is missing. I kept the original extracted
text's line breaks for readability; normalization was used only
in the verification check.