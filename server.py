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
    toggle_upload()
    return render_template("index.html",description=page_description, has_uploaded=has_uploaded)

@app.route("/upload", methods=["POST","GET"])
def upload():
    if request.method == "POST":
        file_pdf = request.files['doc_pdf']
        file_pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], UPLOADED_PDF))

        text = extract_text_from_pdf()
        text_to_speach(text)
        toggle_upload()
        # print(text)
    return home()

if __name__=="__main__":
    app.run(debug=True)