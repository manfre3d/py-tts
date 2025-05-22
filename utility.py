from pyt2s.services import stream_elements
from pdfminer.high_level import extract_text
import os


AUDIO_PATH='static/assets/output.mp3'
UPLOADED_PDF="uploaded_file.pdf"

page_description={
    "page_title": "Text to speech PDF",
    "page_description": "Educational app for Text to speech conversione!\n"
                        "The app aims to take a pdf input and transfot the text of the file in speech that you can play back to yourself",


}

def text_to_speach(text):
    # Default Voice Implementation
    # data = stream_elements.requestTTS('Lorem Ipsum is simply dummy text.')

    # Custom Voice
    data = stream_elements.requestTTS(text, stream_elements.Voice.Russell.value)

    with open(AUDIO_PATH, '+wb') as file:
        file.write(data)

def extract_text_from_pdf():
    pdf_path = f"static/uploads/{UPLOADED_PDF}"
    text = extract_text(pdf_path)
    os.remove(pdf_path)
    return text

def check_upload():
    if os.path.isfile(AUDIO_PATH):
        return True
    else:
        return False

