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

def text_to_speech(text):
    """
    Converts the given text to speech using a custom voice and saves the resulting audio data to a file.
    Args:
        text (str): The text to be converted to speech.
    Returns:
        None
    Notes:
        - Uses the 'stream_elements.requestTTS' function with a custom voice (Russell).
        - The resulting audio data is written to a file specified by AUDIO_PATH.
    """
    
    # Default Voice Implementation
    # data = stream_elements.requestTTS('Lorem Ipsum is simply dummy text.')

    # Custom Voice
    data = stream_elements.requestTTS(text, stream_elements.Voice.Russell.value)

    with open(AUDIO_PATH, '+wb') as file:
        file.write(data)

def extract_text_from_pdf():
    """
    Extracts text content from an uploaded PDF file and removes the file after extraction.
    Returns:
        str: The extracted text from the PDF file.
    Raises:
        FileNotFoundError: If the PDF file does not exist.
        Exception: If there is an error during text extraction or file removal.
    Note:
        Assumes that UPLOADED_PDF is a global variable containing the filename of the uploaded PDF,
        and that extract_text and os modules are properly imported.
    """
    
    pdf_path = f"static/uploads/{UPLOADED_PDF}"
    text = extract_text(pdf_path)
    os.remove(pdf_path)
    return text

def check_upload():
    """
    Checks if the file specified by AUDIO_PATH exists.
    Returns:
        bool: True if the file exists, False otherwise.
    """
    
    if os.path.isfile(AUDIO_PATH):
        return True
    else:
        return False

