from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_pdf_download_returns_400_when_pdf_host_returns_404():
    not_found = MagicMock(status_code=404)

    with patch("api.routes.get_highlights", return_value={}), patch(
        "utils.download.requests.get", return_value=not_found
    ):
        response = client.post(
            "/pdf/download", json={"pdf_url": "https://example.com/missing.pdf"}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to download PDF"
