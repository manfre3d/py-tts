import io
import os
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = '/tmp/test_uploads'
    os.makedirs('/tmp/test_uploads', exist_ok=True)
    with app.test_client() as client:
        yield client


# ── Home route ────────────────────────────────────────────────────────────────

@patch("server.render_template")
@patch("server.os.path.isfile", return_value=False)
def test_home_no_upload_returns_page(mock_isfile, mock_render_template, client):
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_render_template.assert_called_once()
    assert response.data == b"rendered"


@patch("server.render_template")
@patch("server.os.path.isfile", return_value=True)
def test_home_with_job_id_shows_player(mock_isfile, mock_render_template, client):
    with client.session_transaction() as sess:
        sess["job_id"] = "test-job-id"
    mock_render_template.return_value = "rendered"
    response = client.get("/")
    mock_render_template.assert_called_once()
    call_kwargs = mock_render_template.call_args[1]
    assert call_kwargs["has_uploaded"] is True


# ── Upload route ──────────────────────────────────────────────────────────────

@patch("server.threading.Thread")
@patch("server.extract_text")
def test_upload_post_success(mock_extract_text, mock_thread, client):
    mock_extract_text.return_value = "some text"
    mock_thread.return_value = MagicMock()
    with patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
        response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 202
    json_data = response.get_json()
    assert "job_id" in json_data
    mock_extract_text.assert_called_once()
    mock_thread.assert_called_once()


@patch("server.extract_text")
def test_upload_post_exception(mock_extract_text, client):
    mock_extract_text.side_effect = Exception("PDF error")
    with patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
        response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "PDF error" in json_data["message"]


def test_upload_rejects_unsupported_type(client):
    data = {'doc_pdf': (io.BytesIO(b"not valid"), 'test.exe')}
    response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["success"] is False


def test_upload_accepts_txt(client):
    """TXT files are now a supported format."""
    with patch("server.extract_text", return_value="hello world"), \
         patch("server.threading.Thread", return_value=MagicMock()), \
         patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"plain text content"), 'test.txt')}
        response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 202


def test_upload_accepts_docx(client):
    """DOCX files are now a supported format."""
    with patch("server.extract_text", return_value="docx content"), \
         patch("server.threading.Thread", return_value=MagicMock()), \
         patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"fake docx"), 'test.docx')}
        response = client.post("/upload", data=data, content_type='multipart/form-data')
    assert response.status_code == 202


# ── Preview route ─────────────────────────────────────────────────────────────

@patch("server.extract_text")
def test_preview_returns_text(mock_extract_text, client):
    mock_extract_text.return_value = "Hello world this is preview text"
    with patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
        response = client.post("/preview", data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "preview" in json_data
    assert "word_count" in json_data
    assert json_data["word_count"] == 6


def test_preview_rejects_unsupported_type(client):
    data = {'doc_pdf': (io.BytesIO(b"not valid"), 'test.exe')}
    response = client.post("/preview", data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json()["success"] is False


@patch("server.extract_text")
def test_preview_text_truncated_to_500_chars(mock_extract_text, client):
    mock_extract_text.return_value = "A" * 1000
    with patch.object(FileStorage, 'save'):
        data = {'doc_pdf': (io.BytesIO(b"fake pdf content"), 'test.pdf')}
        response = client.post("/preview", data=data, content_type='multipart/form-data')
    json_data = response.get_json()
    assert len(json_data["preview"]) <= 500


# ── Reset route ───────────────────────────────────────────────────────────────

@patch("server.safe_delete_audio")
def test_reset_success(mock_safe_delete, client):
    with client.session_transaction() as sess:
        sess["job_id"] = "test-job-id"
    response = client.post("/reset")
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    mock_safe_delete.assert_called_once()
    with client.session_transaction() as sess:
        assert "job_id" not in sess


@patch("server.safe_delete_audio")
def test_reset_when_no_session(mock_safe_delete, client):
    with client.session_transaction() as sess:
        sess.pop("job_id", None)
    response = client.post("/reset")
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    mock_safe_delete.assert_called_once()


# ── API routes ────────────────────────────────────────────────────────────────

def test_api_voices_returns_list(client):
    response = client.get("/api/voices")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "voices" in json_data
    assert "Matthew" in json_data["voices"]


def test_api_status_returns_bool(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "ai_available" in json_data
    assert isinstance(json_data["ai_available"], bool)
