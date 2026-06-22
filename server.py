from flask import Flask, render_template, request, session, jsonify, url_for
from werkzeug.utils import secure_filename
from utility import page_description, text_to_speech, extract_text_from_pdf, UPLOADED_PDF, AUDIO_PATH, check_upload
import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    import warnings
    warnings.warn("SECRET_KEY not set; using insecure dev key — set it in .env for production")
    app.secret_key = "dev-insecure-key-change-in-production"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_delete_mp3():
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)


@app.route("/", methods=["GET"])
def home():
    if not session.get("upload"):
        safe_delete_mp3()
    has_uploaded = check_upload()
    return render_template("index.html", description=page_description, has_uploaded=has_uploaded)


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file_pdf = request.files.get('doc_pdf')
        if not file_pdf or not allowed_file(file_pdf.filename):
            return jsonify(success=False, message="Only PDF files are allowed."), 400

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filename = secure_filename(file_pdf.filename) or UPLOADED_PDF
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_pdf.save(upload_path)

        try:
            text = extract_text_from_pdf(upload_path)
            text_to_speech(text)
        finally:
            if os.path.exists(upload_path):
                os.remove(upload_path)

        session["upload"] = True
        return jsonify(
            success=True,
            download_url=url_for('static', filename=f'assets/{AUDIO_PATH.split("/")[-1]}', _external=False),
        )

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@app.route("/reset", methods=["POST"])
def reset():
    safe_delete_mp3()
    session.pop("upload", None)
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)
