from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
import os
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_document():

    if "document" not in request.files:
        return jsonify({"error": "No document uploaded"}), 400

    file = request.files["document"]

    if file.filename == "":
        return jsonify({"error": "Please select a PDF"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file"}), 400

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    try:
        reader = PdfReader(filepath)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            return jsonify({
                "error": "Could not extract text from this PDF."
            }), 400

        # Simple summary
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        summary = " ".join(sentences[:5])

        # Important lines
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        important_points = lines[:7]

        # Try to find deadline/date
        deadline = "Not found"

        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)

        if dates:
            deadline = dates[-1]

        result = {
            "summary": summary,
            "important_information": {
                "name": "Not found",
                "department": "Not found",
                "date": dates[0] if dates else "Not found",
                "deadline": deadline
            },
            "important_points": important_points
        }

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/ask", methods=["POST"])
def ask_question():

    data = request.get_json()

    question = data.get("question", "").lower().strip()

    if not question:
        return jsonify({
            "error": "Please enter a question"
        }), 400

    return jsonify({
        "success": True,
        "answer": "This simple demo reads the uploaded PDF. AI question answering will be added in the next version."
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )