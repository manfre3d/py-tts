from flask import (
    Flask, render_template, request, session,
    jsonify, url_for, Response, stream_with_context, send_file,
)
from werkzeug.utils import secure_filename
from utility import (
    page_description, text_to_speech, extract_text,
    UPLOADED_PDF, SUPPORTED_VOICES,
)
from jobs import create_job, push, get_queue, cleanup
import ai_cleanup
import os
import json
import threading
import tempfile
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    import warnings
    warnings.warn("SECRET_KEY not set; using insecure dev key — set it in .env for production")
    app.secret_key = "dev-insecure-key-change-in-production"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_path():
    job_id = session.get("job_id")
    if job_id:
        return f'static/assets/{job_id}.mp3'
    return None


def safe_delete_audio():
    path = get_audio_path()
    if path and os.path.exists(path):
        os.remove(path)


def _conversion_worker(job_id, text, voice, use_ai_cleanup_flag):
    try:
        os.makedirs('static/assets', exist_ok=True)
        if use_ai_cleanup_flag:
            push(job_id, {"status": "cleaning"})
            text = ai_cleanup.clean_text(text)
        output_path = f'static/assets/{job_id}.mp3'

        def on_progress(i, n):
            push(job_id, {"chunk": i, "total": n})

        text_to_speech(text, voice=voice, progress_callback=on_progress, output_path=output_path)
        push(job_id, {"done": True})
    except Exception as e:
        push(job_id, {"error": str(e)})


@app.route("/", methods=["GET"])
def home():
    job_id = session.get("job_id")
    has_uploaded = bool(job_id and os.path.isfile(f'static/assets/{job_id}.mp3'))
    audio_url = url_for('static', filename=f'assets/{job_id}.mp3') if has_uploaded else None
    return render_template(
        "index.html",
        description=page_description,
        has_uploaded=has_uploaded,
        audio_url=audio_url,
        voices=SUPPORTED_VOICES,
    )


@app.route("/upload", methods=["POST"])
def upload():
    file_doc = request.files.get('doc_pdf')
    if not file_doc or not allowed_file(file_doc.filename):
        return jsonify(success=False, message="Only PDF, DOCX, and TXT files are allowed."), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(file_doc.filename) or UPLOADED_PDF
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_doc.save(upload_path)

    try:
        text = extract_text(upload_path)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)

    voice = request.form.get("voice", "Matthew")
    if voice not in SUPPORTED_VOICES:
        voice = "Matthew"
    use_ai = request.form.get("use_ai_cleanup") == "true"

    job_id = create_job()
    session["job_id"] = job_id

    thread = threading.Thread(
        target=_conversion_worker,
        args=(job_id, text, voice, use_ai),
        daemon=True,
    )
    thread.start()

    return jsonify(job_id=job_id), 202


@app.route("/progress/<job_id>")
def progress(job_id):
    q = get_queue(job_id)
    if q is None:
        return jsonify(error="Job not found"), 404

    def generate():
        try:
            while True:
                try:
                    event = q.get(timeout=300)
                except Exception:
                    yield f"data: {json.dumps({'error': 'Processing timed out'})}\n\n"
                    break
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("done") or event.get("error"):
                    break
        finally:
            cleanup(job_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/preview", methods=["POST"])
def preview():
    file_doc = request.files.get('doc_pdf')
    if not file_doc or not allowed_file(file_doc.filename):
        return jsonify(success=False, message="Unsupported file type."), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(file_doc.filename) or UPLOADED_PDF
    tmp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"preview_{filename}")
    file_doc.save(tmp_path)
    try:
        text = extract_text(tmp_path)
        preview_text = text.strip()[:500]
        word_count = len(text.split())
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return jsonify(success=True, preview=preview_text, word_count=word_count)


@app.route("/reset", methods=["POST"])
def reset():
    safe_delete_audio()
    session.pop("job_id", None)
    return jsonify(success=True)


@app.route("/api/status")
def api_status():
    return jsonify(ai_available=ai_cleanup.is_available())


@app.route("/api/voices")
def api_voices():
    return jsonify(voices=SUPPORTED_VOICES)


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """Synchronous REST endpoint: POST a file, receive an MP3."""
    file_doc = request.files.get("file")
    if not file_doc or not allowed_file(file_doc.filename):
        return jsonify(error="Unsupported file type. Accepted: pdf, txt, docx"), 400

    voice = request.form.get("voice", "Matthew")
    if voice not in SUPPORTED_VOICES:
        return jsonify(error=f"Unknown voice. Supported voices: {SUPPORTED_VOICES}"), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(file_doc.filename) or UPLOADED_PDF
    tmp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"api_{filename}")
    tmp_output = os.path.join(tempfile.gettempdir(), f"api_out_{os.urandom(8).hex()}.mp3")

    file_doc.save(tmp_input)
    try:
        text = extract_text(tmp_input)
        text_to_speech(text, voice=voice, output_path=tmp_output)
        return send_file(
            tmp_output,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="converted.mp3",
        )
    except Exception as e:
        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        return jsonify(error=str(e)), 500
    finally:
        if os.path.exists(tmp_input):
            os.remove(tmp_input)


@app.route("/api-docs")
def api_docs():
    return render_template("api_docs.html", voices=SUPPORTED_VOICES)


if __name__ == "__main__":
    app.run(debug=True)
