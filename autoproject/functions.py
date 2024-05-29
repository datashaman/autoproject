import os

import requests

from html_meta_data_parse import HtmlMetaDataParse
from PIL import Image
from playwright.sync_api import sync_playwright
from pydantic import BaseModel
from slugify import slugify
from unstructured.partition.html import partition_html


MAX_IMAGE_SIZE = (2000, 768)


def get_function_list() -> dict:
    """Get a list of the functions that are available to the planner."""
    return {
        "page_metadata": "Fetches metadata from a URL.",
        "page_screenshot": "Creates a screenshot of a URL.",
        "page_scrape": "Scrapes the content of a URL.",
        "search_internet": "Searches the internet for a given query.",
    }


class PageMetadata(BaseModel):
    """Metadata found on a webpage."""

    url: str
    title: str
    description: str
    image: str
    site_name: str
    favicon: str
    keywords: str
    type: str


def page_metadata(url: str) -> PageMetadata:
    """Fetches metadata from a URL."""
    html_meta_data_parse = HtmlMetaDataParse()
    attributes = html_meta_data_parse.get_meta_data_by_url(url)

    # Remove the following attributes, they are not needed
    unneeded_attributes = ["audio", "author", "media", "pubdate"]

    for attribute in unneeded_attributes:
        attributes.pop(attribute, None)

    return attributes


def page_screenshot(url: str) -> str:
    """Creates a screenshot of a URL."""
    attributes = page_metadata(url)
    filename = slugify(attributes.get("site_name") or attributes.get("title")) + ".png"
    screenshot = f"storage/screenshots/{filename}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=screenshot, full_page=True)
        browser.close()

    image = Image.open(screenshot)
    width, height = image.size
    if width > height:
        fit_size = MAX_IMAGE_SIZE
    else:
        fit_size = list(reversed(MAX_IMAGE_SIZE))
    image.thumbnail(fit_size)
    image.save(screenshot)

    return screenshot


def page_scrape(url: str) -> str:
    """Scrapes the content of a URL."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        text = page.content()
        browser.close()

    elements = partition_html(text=text)

    content = "\n\n".join([str(el) for el in elements])
    content = [content[i : i + 8000] for i in range(0, len(content), 8000)]

    return content


def search_internet(query: str, n_results: int = 5) -> dict:
    """Searches the internet for a given query."""
    return requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": os.environ["SERPER_API_KEY"],
        },
        json={"q": query, "num": n_results},
        timeout=(3, 27),
    ).json()
