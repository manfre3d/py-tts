import io
import os
import pytest
from unittest.mock import patch, MagicMock
from server import app, UPLOADED_PDF
from unittest.mock import patch
from server import app


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

@patch("server.os.makedirs")
@patch("server.url_for")
@patch("server.text_to_speech")
@patch("server.extract_text_from_pdf")
@patch("server.toggle_upload")
def test_upload_post_success(mock_toggle_upload, mock_extract_text, mock_tts, mock_url_for, mock_makedirs, client):
    mock_extract_text.return_value = "some text"
    mock_url_for.return_value = "/static/assets/output.mp3"
    data = {
        'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')
    }
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["download_url"] == "/static/assets/output.mp3"
    mock_toggle_upload.assert_called_once()
    mock_extract_text.assert_called_once()
    mock_tts.assert_called_once_with("some text")
    mock_makedirs.assert_called_once()

@patch("server.os.makedirs")
@patch("server.toggle_upload")
@patch("server.extract_text_from_pdf")
def test_upload_post_exception(mock_extract_text, mock_toggle_upload, mock_makedirs, client):
    # Simulate extract_text_from_pdf raising an exception
    mock_extract_text.side_effect = Exception("PDF error")
    data = {
        'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')
    }
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "PDF error" in json_data["message"]
    
@patch("server.safe_delete_mp3")
def test_reset_success(mock_safe_delete_mp3, client):
    # Set session upload to True to test if it is cleared
    with client.session_transaction() as sess:
        sess["upload"] = True

    response = client.post("/reset")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    mock_safe_delete_mp3.assert_called_once()

    # Check that session "upload" is removed
    with client.session_transaction() as sess:
        assert "upload" not in sess

@patch("server.safe_delete_mp3")
def test_reset_when_upload_not_in_session(mock_safe_delete_mp3, client):
    # Ensure "upload" is not in session
    with client.session_transaction() as sess:
        sess.pop("upload", None)

    response = client.post("/reset")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    mock_safe_delete_mp3.assert_called_once()










