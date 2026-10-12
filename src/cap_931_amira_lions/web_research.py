"""
Retrieve text from a public HTML page for sales account research.

This module does not call GPT or generate a report.
It collects source material that we can later give to the model.
"""

# requests sends HTTP requests to websites.
import requests

# BeautifulSoup helps us find content inside a page's HTML.
from bs4 import BeautifulSoup


def fetch_page(url):
    """
    Download one page and return its URL, title, text, and any error.

    url is the website address passed into this function.
    The function returns a dictionary with the same four fields
    whether retrieval succeeds or fails.
    """

    # Start with empty results.
    # None means that no error has been recorded.
    result = {
        "url": url,
        "title": "",
        "text": "",
        "error": None,
    }

    # A try block lets us handle expected network failures
    # instead of allowing them to crash the application.
    try:
        # Ask the website to send this page.
        # The User-Agent identifies our research prototype.
        # The timeout limits how long requests waits for a connection
        # or incoming data; it is not a total download-time limit.
        response = requests.get(
            url,
            headers={
                "User-Agent": "FreedomFlyerResearchPrototype/0.1"
            },
            timeout=20,
        )

        # Raise an exception for unsuccessful HTTP responses.
        # Examples include 404 (not found) and 403 (access denied).
        # The except block below handles these exceptions.
        response.raise_for_status()

        # Read the type of content returned by the website.
        # An empty string is used if the header is missing.
        # Lowercase makes the comparison consistent.
        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        # This function reads HTML, not PDFs or other file formats.
        # Record the problem and return early for unsupported content.
        if "text/html" not in content_type:
            result["error"] = "This source is not an HTML web page."
            return result

        # Convert the downloaded HTML into a searchable structure.
        # html.parser is included with Python.
        soup = BeautifulSoup(response.content, "html.parser")

        # Keep the final address in case the website redirected us.
        # This address will help identify the source of our evidence.
        result["url"] = response.url

        # Save the page title if a title element exists.
        # strip=True removes spaces around the extracted title.
        if soup.title:
            result["title"] = soup.title.get_text(
                " ", strip=True
            )

        # Remove scripts, styling, navigation, and footer content.
        # These elements often add irrelevant text to the research.
        # decompose() removes each selected element from the parsed page.
        for element in soup(
            ["script", "style", "nav", "footer", "noscript"]
        ):
            element.decompose()

        # Use the main element when available.
        # Otherwise, use the body or the entire parsed document.
        # This is a simple extraction approach; some irrelevant
        # content may remain, and some pages may need a different approach.
        content = soup.find("main") or soup.body or soup

        # Extract visible HTML text, separating elements with newlines.
        # This does not execute JavaScript or load content added by it.
        lines = content.get_text(
            separator="\n", strip=True
        ).splitlines()

        # Remove surrounding spaces and discard empty lines.
        # Join the remaining lines into one text string.
        text = "\n".join(
            line.strip()
            for line in lines
            if line.strip()
        )

        # Keep at most 20,000 characters from this page.
        # This limits stored text and helps control later model costs.
        # Characters are not the same as tokens.
        # Truncation can omit useful evidence farther down the page.
        result["text"] = text[:20000]

        # An HTTP request can succeed without returning useful text.
        # Record that situation so the app can explain it to the user.
        if not result["text"]:
            result["error"] = (
                "No readable text was found on this page."
            )

    except requests.RequestException:
        # Handle common request problems, including connection
        # failures, timeouts, and unsuccessful HTTP responses.
        # Return an error message that the interface can display.
        result["error"] = (
            "Could not retrieve this page. It may be unavailable, "
            "blocking automated requests, or taking too long "
            "to respond."
        )

    # Give the collected information back to the calling code.
    # Defining this function does not download anything.
    # A request happens only when code calls fetch_page(url).
    return result