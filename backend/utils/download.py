import os
import requests
import fitz
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_and_highlight_pdf(url: str, highlights: dict) -> bool:
    """
    Download a PDF from URL, highlight specified text, and save both original and highlighted versions.

    :param url: The URL of the PDF file to be downloaded
    :param highlights: Dictionary of highlights for each page
    :return: True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True, timeout=10)

        if response.status_code == 200:
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename.lower().endswith(".pdf"):
                original_filename += ".pdf"

            highlighted_filename = f"highlighted_{original_filename}"

            filepath = os.path.join(os.getcwd(), original_filename)
            with open(filepath, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        pdf_file.write(chunk)

            # Highlight the PDF
            doc = fitz.open(filepath)

            for page_num, sentences_to_highlight in highlights.items():
                if page_num < 0 or page_num >= len(doc):
                    logger.error(f"Invalid page number. PDF has {len(doc)} pages.")
                    return False

                page = doc[page_num]
                text_instances = []
                for sentence in sentences_to_highlight:
                    text_instances.extend(page.search_for(sentence))

                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()

                highlighted_filepath = os.path.join(os.getcwd(), highlighted_filename)
                doc.save(highlighted_filepath, garbage=4, deflate=True)
                logger.info(
                    f"Found and highlighted {len(text_instances)} matches on page {page_num + 1}"
                )

            doc.close()
            return True, original_filename, highlighted_filepath

        else:
            logger.error(
                f"Failed to download file. Status code: {response.status_code}"
            )
            return False

    except requests.RequestException as e:
        logger.error(f"Download error: {e}")
        return False
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return False
