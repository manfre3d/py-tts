from gtts import gTTS
from pdfminer.high_level import extract_text as _pdf_extract_text
import textwrap
import tempfile
import os

AUDIO_PATH = 'static/assets/output.mp3'
UPLOADED_PDF = "uploaded_file.pdf"

SUPPORTED_VOICES = [
    "Matthew", "Joanna", "Amy", "Brian", "Emma",
    "Russell", "Nicole", "Joey",
]

# Maps voice names to gTTS locale accents
_VOICE_TLD = {
    "Matthew": "com",
    "Joanna": "com",
    "Justin": "com",
    "Joey":   "com",
    "Amy":    "co.uk",
    "Brian":  "co.uk",
    "Emma":   "co.uk",
    "Russell": "com.au",
    "Nicole":  "com.au",
}

page_description = {
    "page_title": "PDF to Speech",
    "page_description": (
        "Upload a PDF, DOCX, or TXT file and convert its text to audio. "
        "Choose a voice, optionally clean the text with AI, "
        "then listen or download the generated MP3."
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
        if os.path.exists(path):
            os.remove(path)


def generate_audio_chunks(chunks, voice="Matthew", progress_callback=None):
    tld = _VOICE_TLD.get(voice, "com")
    audio_files = []
    for i, chunk in enumerate(chunks):
        tts = gTTS(text=chunk, lang='en', tld=tld)
        file_name = os.path.join(_TMP_DIR, f"tts_chunk_{i + 1}.mp3")
        tts.save(file_name)
        audio_files.append(file_name)
        if progress_callback:
            progress_callback(i + 1, len(chunks))
    return audio_files


def text_to_speech(text, voice="Matthew", progress_callback=None, output_path=None):
    text = text.strip()
    if not text:
        raise ValueError("No extractable text found in the document.")

    if output_path is None:
        output_path = AUDIO_PATH

    def split_text(t, max_chars=500):
        return textwrap.wrap(t, max_chars, break_long_words=False, break_on_hyphens=False)

    chunks = split_text(text)
    audio_files = generate_audio_chunks(chunks, voice=voice, progress_callback=progress_callback)
    merge_mp3_files_binary(audio_files, output_path)
    delete_chunks(audio_files)


def extract_text_from_pdf(path):
    return _pdf_extract_text(path)


def extract_text_from_txt(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def extract_text_from_docx(path):
    import docx
    doc = docx.Document(path)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(path):
    ext = path.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        return extract_text_from_pdf(path)
    elif ext == 'txt':
        return extract_text_from_txt(path)
    elif ext == 'docx':
        return extract_text_from_docx(path)
    raise ValueError(f"Unsupported file type: .{ext}")


def check_upload():
    return os.path.isfile(AUDIO_PATH)
