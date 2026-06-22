from pyt2s.services import stream_elements
from pdfminer.high_level import extract_text
import textwrap
import tempfile
import os

AUDIO_PATH = 'static/assets/output.mp3'
UPLOADED_PDF = "uploaded_file.pdf"

page_description = {
    "page_title": "Text to speech PDF",
    "page_description": (
        'Educational app for Text to speech conversion and download!\n '
        'Upload your PDF, click "Convert," and after processing, listen '
        'or download the audio.'
    ),
}

_TMP_DIR = tempfile.gettempdir()


def merge_mp3_files_binary(file_paths, output_path):
    with open(output_path, 'wb') as outfile:
        for file_path in file_paths:
            with open(file_path, 'rb') as infile:
                outfile.write(infile.read())


def delete_chunks(audio_files):
    for path in audio_files:
        os.remove(path)


def generate_audio_chunks(chunks):
    audio_files = []
    for i, chunk in enumerate(chunks):
        data = stream_elements.requestTTS(chunk, stream_elements.Voice.Matthew.value)
        file_name = os.path.join(_TMP_DIR, f"tts_chunk_{i + 1}.mp3")
        with open(file_name, 'wb') as file:
            file.write(data)
        audio_files.append(file_name)
    return audio_files


def text_to_speech(text):
    text = text.strip()
    if not text:
        raise ValueError("No extractable text found in the PDF.")

    def split_text(text, max_chars=500):
        return textwrap.wrap(text, max_chars, break_long_words=False, break_on_hyphens=False)

    chunks = split_text(text)
    audio_files = generate_audio_chunks(chunks)
    merge_mp3_files_binary(audio_files, AUDIO_PATH)
    delete_chunks(audio_files)


def extract_text_from_pdf(path):
    return extract_text(path)


def check_upload():
    return os.path.isfile(AUDIO_PATH)
