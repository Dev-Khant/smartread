import os
import re
from mistralai import Mistral
from groq import Groq
from dotenv import load_dotenv

from .prompts import (
    HTML_FORMATTING_PROMPT,
    HIGHLIGHT_PROMPT,
    SEARCHABLE_SENTENCES_PROMPT,
)

load_dotenv()

MISTRAL_CLIENT = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_data(url: str):
    """
    Extract text from a URL using Mistral OCR.

    Args:
        url (str): The URL of the document to extract text from.

    Returns:
        str: The extracted text from the document.
    """
    ocr_response = MISTRAL_CLIENT.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": url},
        include_image_base64=True,
    )
    return ocr_response


def extract_highlights(content: str):
    """
    Extract highlights from a given text using Groq.

    Args:
        content (str): The text to extract highlights from.

    Returns:
        str: The extracted highlights from the text.
    """
    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": HIGHLIGHT_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content


def format_to_html(content: str, highlights: str):
    """
    Format the extracted text and highlights into HTML.

    Args:
        content (str): The extracted text.
        highlights (str): The extracted highlights.

    Returns:
        tuple: A tuple containing:
            - str: The formatted HTML with indexed highlight tags
            - dict: A dictionary mapping highlight indexes to their sentences
    """
    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": HTML_FORMATTING_PROMPT},
            {
                "role": "user",
                "content": f"Markdown text: {content}\n\nList of sentences to highlight: {highlights}",
            },
        ],
        temperature=0.0,
    )

    html_content = response.choices[0].message.content

    # Extract highlight mapping
    highlight_mapping = {}
    highlight_pattern = r'<highlight index=[\'"](\d+)[\'"]>(.*?)</highlight>'
    matches = re.finditer(highlight_pattern, html_content)
    for match in matches:
        index = int(match.group(1))
        sentence = match.group(2)
        highlight_mapping[index] = sentence

    return html_content, highlight_mapping


def extract_searchable_sentences(content: str):
    """
    Extract searchable sentences from a given text using Groq.

    Args:
        content (str): The text to extract searchable sentences from.

    Returns:
        str: The extracted searchable sentences from the text.
    """
    response = GROQ_CLIENT.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SEARCHABLE_SENTENCES_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content
