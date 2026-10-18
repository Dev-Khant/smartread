import base64
from unittest.mock import MagicMock, patch

from utils.db import get_page


URL = "https://example.com/paper.pdf"


def test_get_page_returns_stored_total_pages():
    mock_db = MagicMock()
    mock_db.pages.find_one.return_value = {
        "document_id": base64.b64encode(URL.encode()).decode(),
        "url": URL,
        "page_number": 1,
        "page_data": {"content": base64.b64encode(b"<p>hello</p>").decode()},
        "total_pages": 6,
    }

    with patch("utils.db.db", mock_db):
        page, total_pages = get_page(URL, 1)

    assert total_pages == 6
    assert page["page_data"]["content"] == "<p>hello</p>"


def test_get_page_returns_none_when_not_cached():
    mock_db = MagicMock()
    mock_db.pages.find_one.return_value = None

    with patch("utils.db.db", mock_db):
        page, total_pages = get_page(URL, 1)

    assert page is None
    assert total_pages is None
