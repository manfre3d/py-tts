import json
import pytest
from server import app
from jobs import create_job, push, cleanup


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_progress_invalid_job_returns_404(client):
    response = client.get("/progress/nonexistent-job-id")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_progress_streams_done_event(client):
    job_id = create_job()
    push(job_id, {"done": True})

    response = client.get(f"/progress/{job_id}")
    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    body = response.data.decode()
    assert "done" in body
    assert json.dumps({"done": True}) in body


def test_progress_streams_chunk_event(client):
    job_id = create_job()
    push(job_id, {"chunk": 1, "total": 5})
    push(job_id, {"done": True})

    response = client.get(f"/progress/{job_id}")
    body = response.data.decode()

    assert '"chunk": 1' in body or '"chunk":1' in body
    assert '"total": 5' in body or '"total":5' in body


def test_progress_streams_error_event(client):
    job_id = create_job()
    push(job_id, {"error": "TTS failed"})

    response = client.get(f"/progress/{job_id}")
    body = response.data.decode()
    assert "TTS failed" in body


def test_concurrent_jobs_have_separate_ids():
    from jobs import create_job
    job1 = create_job()
    job2 = create_job()
    assert job1 != job2
    assert f'static/assets/{job1}.mp3' != f'static/assets/{job2}.mp3'
    cleanup(job1)
    cleanup(job2)
