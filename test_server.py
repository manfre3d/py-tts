import io
import pytest
from unittest.mock import patch
from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
    with app.test_client() as client:
        yield client


@patch("server.render_template")
@patch("server.check_upload")
@patch("server.safe_delete_mp3")
def test_home_no_upload_in_session(mock_safe_delete, mock_check_upload, mock_render_template, client):
    with client.session_transaction() as sess:
        sess.pop("upload", None)
    mock_check_upload.return_value = False
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_safe_delete.assert_called_once()
    mock_check_upload.assert_called_once()
    mock_render_template.assert_called_once()
    assert response.data == b"rendered"


@patch("server.render_template")
@patch("server.check_upload")
@patch("server.safe_delete_mp3")
def test_home_with_upload_in_session(mock_safe_delete, mock_check_upload, mock_render_template, client):
    with client.session_transaction() as sess:
        sess["upload"] = True
    mock_check_upload.return_value = True
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_safe_delete.assert_not_called()
    mock_check_upload.assert_called_once()
    mock_render_template.assert_called_once()
    assert response.data == b"rendered"


@patch("server.os.makedirs")
@patch("server.url_for")
@patch("server.text_to_speech")
@patch("server.extract_text_from_pdf")
@patch("server.os.path.exists", return_value=False)
def test_upload_post_success(mock_exists, mock_extract_text, mock_tts, mock_url_for, mock_makedirs, client):
    mock_extract_text.return_value = "some text"
    mock_url_for.return_value = "/static/assets/output.mp3"
    data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["download_url"] == "/static/assets/output.mp3"
    mock_extract_text.assert_called_once()
    mock_tts.assert_called_once_with("some text")
    mock_makedirs.assert_called_once()


@patch("server.os.makedirs")
@patch("server.extract_text_from_pdf")
@patch("server.os.path.exists", return_value=False)
def test_upload_post_exception(mock_exists, mock_extract_text, mock_makedirs, client):
    mock_extract_text.side_effect = Exception("PDF error")
    data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "PDF error" in json_data["message"]


def test_upload_rejects_non_pdf(client):
    data = {'doc_pdf': (io.BytesIO(b"not a pdf"), 'test.txt')}
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["success"] is False


@patch("server.safe_delete_mp3")
def test_reset_success(mock_safe_delete_mp3, client):
    with client.session_transaction() as sess:
        sess["upload"] = True
    response = client.post("/reset")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    mock_safe_delete_mp3.assert_called_once()
    with client.session_transaction() as sess:
        assert "upload" not in sess


@patch("server.safe_delete_mp3")
def test_reset_when_upload_not_in_session(mock_safe_delete_mp3, client):
    with client.session_transaction() as sess:
        sess.pop("upload", None)
    response = client.post("/reset")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    mock_safe_delete_mp3.assert_called_once()
