from flask import Flask, render_template, request
from utility import page_description, text_to_speach, extract_text_from_pdf, UPLOADED_PDF, AUDIO_PATH, check_upload
import os


has_uploaded = False
UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def toggle_upload():
    global has_uploaded
    has_uploaded=check_upload()

@app.route("/")
def home():
    """
    Handles the home route by toggling the upload state and rendering the index page.

    Returns:
        str: Rendered HTML of the index page with the current page description and upload status.
    """
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
    
    if request.method == "POST":
        file_pdf = request.files['doc_pdf']
        file_pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], UPLOADED_PDF))

        text = extract_text_from_pdf()
        text_to_speech(text)
        toggle_upload()
        # print(text)
    return home()

if __name__=="__main__":
    app.run(debug=True)