import io
import os
import pytest
from unittest.mock import patch, MagicMock
from server import app, UPLOADED_PDF


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = './static/uploads'
    with app.test_client() as client:
        yield client

@patch("server.render_template")
@patch("server.toggle_upload")
@patch("server.safe_delete_mp3")
def test_home_no_upload_in_session(mock_safe_delete, mock_toggle_upload, mock_render_template, client):
    # Simulate session without 'upload'
    with client.session_transaction() as sess:
        sess.pop("upload", None)
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_safe_delete.assert_called_once()
    mock_toggle_upload.assert_called_once()
    mock_render_template.assert_called_once()
    assert response.data == b"rendered"

@patch("server.render_template")
@patch("server.toggle_upload")
@patch("server.safe_delete_mp3")
def test_home_with_upload_in_session(mock_safe_delete, mock_toggle_upload, mock_render_template, client):
    # Simulate session with 'upload'
    with client.session_transaction() as sess:
        sess["upload"] = True
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_safe_delete.assert_not_called()
    mock_toggle_upload.assert_not_called()
    mock_render_template.assert_called_once()
    assert response.data == b"rendered"
@patch("server.home")
@patch("server.toggle_upload")
@patch("server.text_to_speech")
@patch("server.extract_text_from_pdf")
@patch("server.os.makedirs")
def test_upload_post_success(
    mock_makedirs,
    mock_extract_text,
    mock_tts,
    mock_toggle_upload,
    mock_home,
    client,
):
    mock_extract_text.return_value = "dummy text"
    mock_home.return_value = "home rendered"
    data = {
        "doc_pdf": (io.BytesIO(b"PDF content"), "test.pdf")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data")
    mock_makedirs.assert_called_once()
    mock_extract_text.assert_called_once()
    mock_tts.assert_called_once_with("dummy text")
    mock_toggle_upload.assert_called_once()
    mock_home.assert_called_once()
    assert response.data == b"home rendered"

@patch("server.home")
def test_upload_get_returns_home(mock_home, client):
    mock_home.return_value = "home rendered"
    response = client.get("/upload")
    mock_home.assert_called_once()
    assert response.data == b"home rendered"


