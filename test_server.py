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

@patch("server.extract_text_from_pdf")
@patch("server.text_to_speech")
@patch("server.toggle_upload")
def test_upload_post_success(mock_toggle_upload, mock_text_to_speech, mock_extract_text_from_pdf, client):
    # Mock extract_text_from_pdf to return some text
    mock_extract_text_from_pdf.return_value = "Sample text"
    mock_text_to_speech.return_value = None
    mock_toggle_upload.return_value = None

    # Create a dummy PDF file
    data = {
        'doc_pdf': (io.BytesIO(b"dummy pdf content"), 'test.pdf')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)

    # Check that the mocks were called
    mock_extract_text_from_pdf.assert_called_once()
    mock_text_to_speech.assert_called_once_with("Sample text")
    mock_toggle_upload.assert_called()

    # Check that the file was saved
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], UPLOADED_PDF)
    assert os.path.exists(saved_path)
    os.remove(saved_path)  # Clean up

    # Check that the response is valid HTML (index page)
    assert response.status_code == 200
    assert b"<html" in response.data or b"<!DOCTYPE html" in response.data

def test_upload_get(client):
    response = client.get('/upload')
    # Should return the home page (index)
    assert response.status_code == 200
    assert b"<html" in response.data or b"<!DOCTYPE html" in response.data