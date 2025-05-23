from gtts import gTTS
from pyt2s.services import stream_elements
from pdfminer.high_level import extract_text
import textwrap
import os

AUDIO_PATH='static/assets/output.mp3'
UPLOADED_PDF="uploaded_file.pdf"

page_description={
    "page_title": "Text to speech PDF",
    "page_description": 'Educational app for Text to speech conversion and download!\n '
                        'Upload your PDF, click "Convert," and after processing, listen '
                        'or download the audio.'

}
def merge_mp3_files_binary(file_paths, output_path):
    """
    Merges multiple MP3 files into a single output file using binary concatenation.
    Args:
        file_paths (list of str): List of paths to the MP3 files to be merged, in the desired order.
        output_path (str): Path where the merged MP3 file will be saved.
    """
    with open(output_path, 'wb') as outfile:
        for file_path in file_paths:
            with open(file_path, 'rb') as infile:
                outfile.write(infile.read())


def delete_chunks(audio_files):
    """
    Deletes the specified audio files from the filesystem.
    Args:
        audio_files (list of str): A list of file paths to audio files that should be deleted.
    """
    for path in audio_files:
        os.remove(path)
def generate_audio_chunks(chunks):
    """
    Generate document audio chunks
    Args:
        chunks (list): List of text chunks to be converted to audio.
    Returns:
        list: List of file paths for the generated audio files.
    """    
    audio_files=[]
    for i, chunk in enumerate(chunks):
        data = stream_elements.requestTTS(chunk, stream_elements.Voice.Matthew.value)
        file_name = f"{AUDIO_PATH.split('.')[0]}{i + 1}.mp3"
        with open(file_name, '+wb') as file:
            file.write(data)
        # tts = gTTS(chunk, lang='en')
        # tts.save(file_name)
        audio_files.append(file_name)
    return audio_files

def text_to_speech(text):
    """
    Converts the given text to speech using a custom voice and saves the resulting audio data to a file.
    Args:
        text (str): The text to be converted to speech.
    Returns:
        None
    """
    
    def split_text(text, max_chars=500):
        """
        Splits the text into chunks of a specified maximum number of characters (default 500).
        Args:
            text (str): The text to be split.
            max_chars (int): The maximum number of characters per chunk.
        Returns:
            list: A list of text chunks, each with a maximum length of max_chars.
        """
        return textwrap.wrap(text, max_chars, break_long_words=False, break_on_hyphens=False)

    chunks = split_text(text)

    audio_files = generate_audio_chunks(chunks)
    merge_mp3_files_binary(audio_files, AUDIO_PATH)
    delete_chunks(audio_files)

def extract_text_from_pdf(path):
    """
    Extracts text content from an uploaded PDF file and removes the file after extraction.
    Returns:
        str: The extracted text from the PDF file.
    """

    text = extract_text(path)
    os.remove(path)
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

