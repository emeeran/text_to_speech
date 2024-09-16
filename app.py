from flask import Flask, render_template, request, send_from_directory, jsonify
from gtts import gTTS
from pydub import AudioSegment
import os
import PyPDF2
import docx
import markdown
from ebooklib import epub
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)


from pydub import AudioSegment
import os


def adjust_pitch(sound, octaves):
    """Adjust the pitch of the sound."""
    new_sample_rate = int(sound.frame_rate * (2.0**octaves))
    pitched_sound = sound._spawn(
        sound.raw_data, overrides={"frame_rate": new_sample_rate}
    )
    return pitched_sound.set_frame_rate(44100)


def convert_text_to_speech(text, gender):
    """Generate audio based on gender and save it."""
    tts = gTTS(text=text, lang="en", slow=False)
    audio_file = os.path.join(AUDIO_FOLDER, "output.mp3")
    tts.save(audio_file)

    if gender == "male":
        # Load the generated audio
        sound = AudioSegment.from_mp3(audio_file)
        # Apply pitch adjustment (lower pitch by shifting down an octave)
        sound = adjust_pitch(
            sound, -0.3
        )  # Lower the pitch slightly without changing speed
        sound.export(audio_file, format="mp3")  # Overwrite the audio file

    return audio_file


def extract_text_from_file(file_path, file_type):
    """Extract text based on file type (PDF, DOCX, MD, TXT, EPUB)."""
    text = ""

    if file_type == "pdf":
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()

    elif file_type == "docx":
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

    elif file_type == "md":
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()
            text = markdown.markdown(markdown_text)

    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    elif file_type == "epub":
        book = epub.read_epub(file_path)
        for item in book.get_items_of_type(epub.EpubHtml):
            soup = BeautifulSoup(item.content, "html.parser")
            text += soup.get_text()

    return text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    text = request.form.get("text", None)
    gender = request.form.get("voice", "female")
    file = request.files.get("file")

    if file:
        file_type = file.filename.split(".")[-1].lower()
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        if file_type in ["pdf", "docx", "md", "txt", "epub"]:
            text = extract_text_from_file(file_path, file_type)

    if text:
        audio_file = convert_text_to_speech(text, gender)
        return jsonify({"audio_file": "output.mp3"})

    return jsonify({"error": "No text provided"})


@app.route("/audio/<filename>")
def play_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
