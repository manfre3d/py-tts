from flask import Flask, render_template, request, session, jsonify, url_for
from utility import page_description, text_to_speech, extract_text_from_pdf, UPLOADED_PDF, AUDIO_PATH, check_upload
import os
from dotenv import load_dotenv

load_dotenv()

has_uploaded = False
UPLOAD_FOLDER = '/tmp/uploads'
pdf_path = os.path.join(UPLOAD_FOLDER, UPLOADED_PDF)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = os.getenv("SECRET_KEY")

def toggle_upload():
    global has_uploaded
    has_uploaded=check_upload()
def safe_delete_mp3():
    file_path = "static/assets/output.mp3"
    if os.path.exists(file_path):
        os.remove(file_path)

@app.route("/",methods=["POST","GET"])
def home():
    """
    Handles the home route by toggling the upload state and rendering the index page.
    Returns:
        str: Rendered HTML of the index page with the current page description and upload status.
    """

    if not session.get("upload"):
        safe_delete_mp3()
        toggle_upload()

    return render_template("index.html",description=page_description, has_uploaded=has_uploaded)

@app.route("/upload", methods=["POST","GET"])
def upload():
    """
    Handles file upload via POST request, saves the uploaded PDF to the server, extracts text from the PDF,
    converts the extracted text to speech, toggles the upload state, and returns the home page.
    Returns:
        Response: The rendered home page after processing the uploaded file.
    """
    try:
        if request.method == "POST":

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            file_pdf = request.files['doc_pdf']
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], UPLOADED_PDF)
            file_pdf.save(upload_path)

            text = extract_text_from_pdf(upload_path)
            text_to_speech(text)
            toggle_upload()
            session["upload"]=True
            # toggle_upload()

            return jsonify(success=True,
                           download_url=url_for('static', filename=f'assets/{AUDIO_PATH}', _external=False))

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

if __name__=="__main__":
    app.run(debug=True)