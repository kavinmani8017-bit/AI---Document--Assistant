import os
import json

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from google import genai
from google.genai import types


# Load .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Please add it to the .env file."
    )


# Gemini client
client = genai.Client(api_key=API_KEY)


# Flask app
app = Flask(__name__)


# Upload folder
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# Allowed files
ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg"
}


# Store current document
current_document = None


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# Home page
@app.route("/")
def home():

    return render_template("index.html")


# Analyze document
@app.route("/analyze", methods=["POST"])
def analyze_document():

    global current_document

    if "document" not in request.files:

        return jsonify({
            "error": "No document uploaded."
        }), 400


    file = request.files["document"]


    if file.filename == "":

        return jsonify({
            "error": "Please select a document."
        }), 400


    if not allowed_file(file.filename):

        return jsonify({
            "error": "Only PDF, JPG, JPEG and PNG files are allowed."
        }), 400


    try:

        # Save uploaded file
        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)


        # Upload file to Gemini
        current_document = client.files.upload(
            file=filepath
        )


        # AI prompt
        prompt = """
You are an AI document understanding assistant.

Analyze the uploaded document carefully.

Return ONLY valid JSON.

Use exactly this structure:

{
  "document_type": "",
  "summary": "",
  "important_information": {
    "name": "",
    "register_number": "",
    "department": "",
    "date": "",
    "deadline": "",
    "organization": ""
  },
  "important_points": []
}

Instructions:

1. Identify the document type.
2. Give a short and clear summary.
3. Extract important information.
4. If a field is not available, use "Not found".
5. Give 3 to 7 important points.
6. Do not invent information.
"""


        response = client.models.generate_content(

            model=MODEL,

            contents=[
                prompt,
                current_document
            ],

            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )


        # Convert AI response to JSON
        data = json.loads(response.text)


        return jsonify({
            "success": True,
            "data": data
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# Ask question
@app.route("/ask", methods=["POST"])
def ask_question():

    global current_document


    if current_document is None:

        return jsonify({
            "error": "Please upload and analyze a document first."
        }), 400


    data = request.get_json()

    question = data.get("question", "").strip()


    if not question:

        return jsonify({
            "error": "Please enter a question."
        }), 400


    try:

        prompt = f"""
You are an AI document assistant.

Answer the user's question using ONLY
the information available in the uploaded document.

If the answer cannot be found in the document,
clearly say that the information is not available.

User question:

{question}
"""


        response = client.models.generate_content(

            model=MODEL,

            contents=[
                prompt,
                current_document
            ]
        )


        return jsonify({
            "success": True,
            "answer": response.text
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# Run application
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )