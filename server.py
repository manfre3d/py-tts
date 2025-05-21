from flask import Flask, render_template, request
from utility import page_description
from pyt2s.services import stream_elements

def text_to_speach():
    # Default Voice Implementation
    # data = stream_elements.requestTTS('Lorem Ipsum is simply dummy text.')

    # Custom Voice
    data = stream_elements.requestTTS('Lorem Ipsum is simply dummy text.', stream_elements.Voice.Russell.value)

    with open('static/assets/output.mp3', '+wb') as file:
        file.write(data)


UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html",description=page_description)
@app.route("/upload", methods=["POST","GET"])
def upload():
    if request.method == "POST":

        file_pdf = request.files['doc_pdf']

    return home()

if __name__=="__main__":
    app.run(debug=True)