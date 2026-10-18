# CAP 931 - FreedomFlyer Sales Assistant

**Author:** Amira Lions  
**Repository:** https://github.com/AmiraLions/CAP_931_Amira_Lions  
**Status:** Working local prototype; human factual review required. Not deployed to production.

## Overview

I built a Python and Streamlit prototype to help a sales representative research a prospective account and prepare a sourced sales brief. The app collects sales inputs, downloads public HTML pages, optionally extracts product-document text, and uses two chained OpenAI requests to produce research findings and a draft report.

The app provides local report checks, experiment downloads, and one-page PDF export. These checks do not establish factual accuracy. My experiments showed that plausible, cited drafts can still contain unsupported conclusions. The reviewed submission candidate was edited after generation and checked against saved evidence; it is not presented as an unedited model output.

## Sales Scenario

| Input | Selected scenario |
|---|---|
| Product | FreedomFlyer, a fictional proposed brand |
| Category | Electric luxury Class B motorhomes |
| Prospect | Sunshine State RVs, Gainesville, Florida |
| Prospect website | https://www.sunshinestatervs.com/ |
| Target contact | Nick Schmidt, General Manager/Owner |
| Title evidence | https://www.sunshinestatervs.com/--xstaff |
| Competitor brands | Coachmen RV, Winnebago, Midwest Automotive Designs, Noovo, Roadtrek, Tiffin |

**Value proposition:** FreedomFlyer offers electric luxury Class B motorhomes with zero tailpipe emissions and an expandable solar system designed to support beautiful advantures!

"Advantures" is intentional brand wording. All product specifications are proposed design targets. Engineering feasibility, range, solar output, battery integration, price, and availability are unvalidated. A verified job title does not independently establish a person's purchasing authority.

## Implemented Features

- Editable product name, prospect URL, product category, competitor URLs, value proposition, and target-contact fields.
- Optional additional prospect URLs, prefilled with the staff page and five new-inventory pages.
- Required-field and basic HTTP/HTTPS URL-format checks.
- HTML retrieval with timeouts, extraction previews, and error handling.
- Conservative detection of common short error-only and access-check pages, including an observed Travato error response.
- Optional PDF/TXT product upload with a preview and an explicit control for inclusion in OpenAI requests.
- Uploaded product context kept separate from independently retrieved source records.
- Research extraction followed by report drafting through prompt chaining.
- Known-source reference construction, including IDs within grouped or ranged citation markers.
- Local checks for body word count, required headings, source IDs, citation formatting, numbered discovery questions, and selected brand wording.
- Markdown and JSON experiment downloads containing findings, usage, checks, and evidence.
- Saved-experiment JSON loading without a new model request.
- Editable report text and one-page PDF preparation with clickable references.

## Setup and Reproduction

### Prerequisites

- Git and uv installed.
- Access to the repository; it may require GitHub authentication.
- Internet access for package installation, web retrieval, and model requests.
- An OpenAI API project with usable credit and model access for live generation. API usage is separate from a ChatGPT subscription.

The project pins Python **3.14.7** in `.python-version`. Exact dependency resolutions are recorded in `uv.lock`. Reproduction still depends on compatible package distributions and external-service availability.

### Create a local checkout

Run these commands one at a time in PowerShell:

```powershell
git clone https://github.com/AmiraLions/CAP_931_Amira_Lions.git
cd CAP_931_Amira_Lions
uv sync --locked
```

`uv sync --locked` creates/synchronizes the environment using the committed lock file and fails if the project requirements require a lock update. It does not intentionally upgrade dependencies. uv may download the pinned Python version if needed and available.

### Configure local credentials

Create a file named `.env` in the project root, alongside `pyproject.toml`:

```dotenv
OPENAI_API_KEY=replace_with_your_own_key
OPENAI_MODEL=gpt-4.1-mini
```

The value above is a placeholder, not a working key. Keep real keys out of code, screenshots, reports, and Git. `.gitignore` excludes `.env` and the named local API-key backup pattern. A local `.env` file is not encrypted storage.

The client loads `.env` explicitly with python-dotenv. VS Code terminal environment injection is not required. An existing process environment setting may take precedence over `.env`.

### Start the app

From the project root:

```powershell
uv run python -m streamlit run src/cap_931_amira_lions/app.py --server.address 127.0.0.1
```

Open the Local URL printed in the terminal. The server is bound to the local computer. Press **Ctrl+C** in the terminal to stop it.

This module-based launch worked on my Windows computer after Application Control blocked the separate `streamlit.EXE` launcher. It does not change Windows security settings; behavior on other managed computers depends on their policies.

## How to Use the App

1. Review or edit the form fields and click **Review Inputs**. Submit changes before using them for retrieval or generation.
2. Optionally upload a product PDF or TXT file. Review its extracted text. Leave inclusion unchecked for local preview only, or check inclusion to send that text during generation.
3. Click **Retrieve Web Evidence**. Review successful text and failed-source messages; availability and listings can change.
4. Click **Generate Sales Brief** once when ready. This sends two paid requests to OpenAI. Inspect the draft, findings, source records, usage, and automatic warnings.
5. Download the experiment record and evidence snapshot. These contain submitted inputs and included product text; inspect them before sharing private material.
6. For a saved run, use **Open a Saved Experiment**, upload the app's JSON snapshot, and click **Load Saved Experiment**. Loading does not call GPT.
7. Review or edit the PDF body, click **Prepare PDF**, then download it. PDF preparation is local and does not verify factual correctness.

A new form submission clears earlier research and report results. Removing an uploaded product file and resubmitting clears its saved product text. Session data is not a durable project database and can be lost when the session ends.

## Code Organization

| File | Responsibility |
|---|---|
| `src/cap_931_amira_lions/app.py` | Interface, validation, session state, uploads, saved runs, downloads |
| `src/cap_931_amira_lions/web_research.py` | HTTP retrieval, HTML text extraction, page-quality screening |
| `src/cap_931_amira_lions/document_reader.py` | In-memory PDF/TXT extraction and upload limits |
| `src/cap_931_amira_lions/prompts.py` | Shared boundaries and research/report instructions |
| `src/cap_931_amira_lions/llm_client.py` | Two API calls, source IDs, citation parsing, local checks, usage and snapshots |
| `src/cap_931_amira_lions/report_generator.py` | PDF layout, source links, and one-page verification |
| `api_check.py` | Small, paid API connectivity test |
| `pdf_check.py` | Local PDF test using the reviewed brief and saved evidence |
| `pyproject.toml`, `uv.lock`, `.python-version` | Package requirements, resolved dependencies, Python pin |
| `.gitignore`, `.gitattributes` | Credential/artifact exclusions and binary-file handling |

The implementation uses two sequential model roles through prompt chaining. It is not a framework of independently acting autonomous agents.

## Model Selection and Prompt Experiments

I selected **GPT-4.1 mini** as a starting point for instruction following, latency, and low text-processing cost. Successful API responses reported `gpt-4.1-mini-2025-04-14`. I did not run a controlled comparison with another model, so I do not claim it is the best-performing choice.

The initial connection test on October 12, 2026 returned **API connection successful**, using 14 input tokens and 4 output tokens.

The research step receives source text and account inputs. The report step receives the research findings and source references. Included product text is labeled unverified user-provided context in both steps. Instructions request task focus, evidence attribution, fictional-product labeling, and resistance to commands embedded in source data. These are mitigations, not guarantees.

| Experiment | Readable sources | Input tokens, both steps | Output tokens, both steps | Observed outcome |
|---|---:|---:|---:|---|
| 1 | 9/15 | 9,604 | 1,910 | Workflow succeeded; missing dealership evidence led to unsupported relationship conclusions |
| 2 | 14/20 | 35,248 | 2,387 | Added five inventory pages and revised prompts; improved brand coverage, but overstatement and scope errors remained |
| 3 | 14/20 | 35,238 | 2,148 | Automatic checks flagged 462 body words and grouped citations; factual errors remained |
| 4 | 13/20 | 36,857 | 2,203 | Uploaded product context reached the model; Travato error text was excluded; 476 words and recurring factual/format errors remained |

These are developmental experiments, not a controlled benchmark. Inputs, prompt instructions, code, and retrieval conditions changed between runs. Improvements cannot be attributed to one change alone. The original experiment records remain unchanged for comparison.

## Validation and Evidence

The following manual results were observed and reported by me during development. Additional simulated checks performed with AI assistance are described separately below.

| Test | Result |
|---|---|
| Blank product name | Required-field error; report-input review withheld |
| Prospect URL entered as `hello` | URL-format error |
| `hello` added as competitor entry 14 | Entry-specific URL error |
| Original valid inputs restored | Success message and input review |
| Staff-page retrieval | Nick Schmidt and General Manager/Owner found after whitespace-normalized comparison |
| Grouped citation parsing | `[S1-S3] [S5,S6]` produced S1, S2, S3, S5, S6 |
| Travato error-only page | Warning displayed; excluded from usable evidence |
| Valid TXT and text-based product PDF | Text extracted; PDF preview showed 870 characters |
| Empty file, unsupported DOCX, damaged PDF | Helpful rejection without interface crash |
| Upload sharing unchecked/checked | Preview-only/inclusion messages changed as expected |
| Upload removal and form resubmission | Prior document preview and text cleared |
| Upload-to-report generation | Snapshot recorded included product context; Experiment 4 generated |
| Reviewed brief PDF generation | Exactly one page; visual layout inspected |
| Saved JSON loading and Streamlit PDF download | Loaded without regeneration; one-page download inspected |

AI-assisted local checks used saved source text and simulated API/UI behavior to exercise citation parsing, unknown IDs, error-page screening, document inclusion, removal, and invalid inputs. They were not live production or security certification tests and did not incur API charges.

Evidence screenshots are in `src/cap_931_amira_lions/screenshots/`:

1. `01_input_form.png`
2. `02_missing_product.png`
3. `03_invalid_prospect_url.png`
4. `04_invalid_competitor_url.png`
5. `05_valid_inputs.png`
6. `06_staff_page_retrieval.png`
7. `07_product_document_preview.png`
8. `08_pdf_export.png`

## Reports and Experiment Records

- `reports/FreedomFlyer_reviewed_sales_brief.pdf`: reviewed submission candidate; edited after generation and checked against saved evidence, not a fresh inventory verification.
- `reports/experiment_04_pdf_export_test.pdf`: export-function test using the unapproved Experiment 4 draft; not the final factual report.
- `src/cap_931_amira_lions/experiments/`: original drafts, snapshots, and `freedomflyer_reviewed_brief.md` with editorial revision notes.
- `FreedomFlyer_product_overview.pdf`: fictional product context used to test extraction and inclusion.

The Per Scholas KB report template supplies the technical report structure: title page, Overview, Steps with screenshots, Conclusion, and Appendix. It is separate from the app's custom one-page sales-brief layout. Final instructor-facing documentation should distinguish the generated drafts from the reviewed sample.

## Challenges and Solutions

### Website whitespace caused a false-negative name match

The staff page contained extra spaces and line breaks within Nick Schmidt's name. I inspected the retrieved text, then used `" ".join(text.split()).lower()` for the verification comparison. Both the name and title were found. Original line breaks were retained in the preview.

### Missing evidence became unsupported conclusions

Early drafts suggested the dealership did not carry brands absent from the initially retrieved pages. I added all five new-inventory page URLs, inspected actual entries marked NEW, and strengthened evidence instructions. Later drafts still overgeneralized, demonstrating the need for human review.

### An HTTP-success page contained an error message

The Travato page returned interface/error text despite a technically successful request. I added conservative page-quality screening. The observed response is now excluded; the heuristic does not detect every possible unusable page.

### Grouped citations lost source references

The original checker recognized only individual markers. I added extraction of grouped and ranged IDs so known references are retained. Nonstandard formatting is still flagged, and unknown IDs do not receive invented URLs.

### File-transfer and naming problems

Some copied file previews ended at line 128, and a downloaded file was named `llm_client (1).py`. I checked complete-file end markers, restored complete contents, corrected the filename, and verified imports before continuing.

### PDF line-ending warnings in Git

I added `.gitattributes` rules treating PDFs and PNGs as binary, restaged the PDFs, and confirmed text conversion was disabled.

## Known Limitations

- Model outputs can contain factual errors, unsupported absence claims, scope drift, and incorrect availability generalizations, even with citations.
- Mechanical checks do not verify whether evidence supports a sentence. Their warnings are advisory, not an approval gate.
- PDF preparation checks page count, not factual accuracy or automatic enforcement of every report-quality warning. It tries body sizes down to nine points, then rejects content that does not fit rather than truncating it.
- Retrieval reads supplied HTML URLs; it does not perform comprehensive web search, execute JavaScript, or automatically discover pagination. Pages are limited to 20,000 extracted characters each.
- Website availability, inventory, redirects, and layouts can change. A saved snapshot is historical evidence, not a guarantee of current stock.
- PDF/TXT uploads are limited to 5 MB; PDFs to 30 pages; retained text to 20,000 characters. No OCR, encrypted PDF support, DOCX, or deck parsing is implemented.
- File extensions and parser checks do not constitute malware scanning or resource-isolated processing.
- The app has no implemented account authentication, authorization, production job queue, scheduled alerts, or durable database.
- Basic URL checks do not provide production-grade protection against requests to internal/private network addresses or malicious redirects.
- Prompt constraints and untrusted-data labels do not eliminate prompt injection.
- A partial model workflow may incur charges before a later failure. Usage displays do not replace billing records.

## Proposed Production Deployment Plan

This section is a plan, not a claim that production controls or deployment already exist.

### Hosting and reproducibility

Package the app in a supported container runtime with the committed Python/dependency specifications. Validate those versions on the intended host. Use separate development, staging, and production configurations, automated startup checks, HTTPS, and authenticated access. Store API credentials in the hosting provider's secret manager rather than a committed file.

### Security and privacy

Before external use, restrict outbound retrieval with network controls and URL/redirect validation that excludes loopback, private, link-local, and infrastructure metadata destinations. Add request-size and response-size limits. Isolate document parsing with resource/time limits and file scanning appropriate to the environment. Add authorization, upload consent, retention/deletion rules, and audit logging that excludes secrets and unnecessary document text. Redact sensitive content in logs and downloads. Rotate or revoke keys as needed.

### Scalability and cost

Move retrieval and model work into a bounded job queue with worker limits, cancellation, and per-user quotas. Respect source-site access policies and implement caching with freshness timestamps. Use bounded retry/backoff only for appropriate transient failures, with duplicate-request and cost awareness. Set provider budgets/alerts, instrument token usage and latency, and limit input size before model calls. Verify whether provider budget controls are alerts or enforced limits.

### Quality, maintenance, and release process

Maintain fixed test snapshots plus periodically refreshed cases for source attribution, inventory conditions, document handling, prompt injection, and factual errors. Add automated source/claim checks and a human approval step before external sales use. Run dependency/security checks and smoke tests in CI. Evaluate model or prompt changes in staging, track versions, and retain a rollback path through Git/container versions. Monitor retrieval failure rates, model failures, response time, and report-quality trends.

### Optional alert-system design

A future service could periodically check approved sources for selected keywords, compare new content with stored hashes/timestamps, and queue deduplicated notifications. Email would require verified recipients, explicit opt-in, unsubscribe controls, delivery monitoring, and rate limits. No alert emails or scheduler are implemented in this prototype.

### Future model extensions

A document/vision-capable model could help interpret product decks or images; a separate presentation-generation component could prepare meeting slides from approved findings. Any such extension would require authorization for supplied documents, source preservation, model evaluation, and human review. These extensions are proposed, not implemented.

## Time Management

The following figures are reconstructed from conversation timestamps and
my recollection, not a continuously measured time log. Session windows
may contain short pauses and do not equal verified active coding hours.
Known breaks and interruptions were excluded where identifiable; longer
unconfirmed gaps were omitted. Independent work may be missing.

| Task group / date | Approximate time | Work and reason for allocation |
|---|---:|---|
| Product and account planning | 3 hours, learner estimate | Defined the fictional product, prospect, contact, competitors, and research inputs before implementation |
| October 11 | 30 minutes, partial window | Validation testing and documentation checkpoint; only the 5:47–6:17 p.m. window is included, not the entire evening |
| October 12 | 7 hours, reconstructed windows | Reproducibility, GitHub, API setup, retrieval, interface testing, screenshots, prompt chaining, and Experiments 1–2; integration and troubleshooting occupied most of the day |
| October 14 | 1 hour 40 minutes, reconstructed windows | Preserved experiments, revised modules, repaired incomplete file transfers, checked imports, and generated Experiment 3 |
| October 16 | 2 hours 25 minutes, reconstructed windows | Reviewed evidence, fixed citations and page screening, added/tested document uploads, saved Experiment 4, and developed/tested PDF output |

**Partial planning/session-window subtotal: approximately 14 hours
35 minutes.** This combines one learner estimate with reconstructed
windows; it is not a precise active-work total. October 7, October 9,
additional October 11 work, and October 17 are not included as separately
estimated workdays. The planning estimate may cover planning activity
from those earlier dates and must not be counted again.

All session times used for reconstruction are Pacific time. Known
October 12 exclusions include the morning and lunch breaks, a 20-minute
calendar interruption, a restroom/food break, and roughly one hour away.
October 14 excludes the class-introduction gap and the reported
break/instructor meeting. Longer unconfirmed October 16 gaps were
omitted. Class attendance alone was not counted as project work.

October 17 work is still in progress. I returned from an errand at
approximately 4:32 p.m.; the errand is excluded. Additional time should
be recorded separately rather than inferred from the entire elapsed day.

The allocation reflects learning, implementation, testing, and debugging,
not just typing code. Two-hour work blocks and planned 30-minute breaks
were used when practical. The complete project total remains uncertain.

## Learning and Assistance

I used AI assistance for explanations, commented code examples, troubleshooting, code review, and documentation. I ran the local commands, tested the interface, inspected outputs, saved evidence, and managed Git checkpoints. This disclosure does not replace the individual requirement to understand and explain the implementation.

Key takeaways were separating code from terminal commands, reproducing environments with pins and locks, tracing failures through modules, distinguishing retrieval success from useful evidence, and treating model-generated sales claims as drafts requiring review.

## Remaining Submission Tasks

- Review this README for accuracy and finalize any honest time estimates.
- Complete the Per Scholas technical report with selected screenshots and experiment comparisons.
- Include the reviewed one-pager and clearly distinguish it from unapproved experiment outputs.
- Complete the final reproduction/smoke checks and confirm grader access to the private repository.
- Commit and push final documentation and deliverables.
