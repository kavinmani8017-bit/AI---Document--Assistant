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


def find_section(text, keywords):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for i, line in enumerate(lines):

        line_lower = line.lower()

        # Check if any keyword is present
        if any(keyword.lower() in line_lower for keyword in keywords):

            result = line

            # Add next 2 lines for more context
            if i + 1 < len(lines):
                result += " " + lines[i + 1]

            if i + 2 < len(lines):
                result += " " + lines[i + 2]

            return result[:1200]

    # Try matching individual words
    for keyword in keywords:

        words = keyword.lower().split()

        for i, line in enumerate(lines):

            if any(word in line.lower() for word in words):

                result = line

                if i + 1 < len(lines):
                    result += " " + lines[i + 1]

                return result[:1200]

    return "Relevant information was not clearly found in the document."

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

        # SUMMARY

        sentences = re.split(
            r'(?<=[.!?])\s+',
            text.strip()
        )

        summary = " ".join(sentences[:5])

        # IMPORTANT POINTS

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        important_points = lines[:7]

        # NAME

        name = "Not found"

        name_patterns = [
            r'(?i)(?:name|student name|candidate name)\s*[:\-]\s*([A-Za-z][A-Za-z .]{2,50})',
            r'(?i)(?:applicant name)\s*[:\-]\s*([A-Za-z][A-Za-z .]{2,50})'
        ]

        for pattern in name_patterns:

            match = re.search(pattern, text)

            if match:
                name = match.group(1).strip()
                break

        # DEPARTMENT

        department = "Not found"

        department_patterns = [
            r'(?i)(?:department|dept)\s*[:\-]\s*([A-Za-z &/.-]{2,80})',
            r'(?i)(?:branch)\s*[:\-]\s*([A-Za-z &/.-]{2,80})',
            r'(?i)(?:course)\s*[:\-]\s*([A-Za-z &/.-]{2,80})'
        ]

        for pattern in department_patterns:

            match = re.search(pattern, text)

            if match:
                department = match.group(1).strip()
                break

        # DATE

        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b',
            r'\b[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}\b'
        ]

        dates = []

        for pattern in date_patterns:

            found_dates = re.findall(pattern, text)
            dates.extend(found_dates)

        date = dates[0] if dates else "Not found"

        deadline = dates[-1] if dates else "Not found"

        # RESULT

        result = {

            "summary": summary,

            "important_information": {

                "name": name,

                "department": department,

                "date": date,

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


# ASK YOUR DOCUMENT

@app.route("/ask", methods=["POST"])
def ask_question():

    data = request.get_json()

    question = data.get(
        "question",
        ""
    ).lower().strip()

    if not question:

        return jsonify({
            "error": "Please enter a question"
        }), 400

    # Find uploaded PDF

    files = os.listdir(
        app.config["UPLOAD_FOLDER"]
    )

    if not files:

        return jsonify({
            "error": "Please upload a document first."
        }), 400

    # Get latest PDF

    pdf_files = [
        f for f in files
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:

        return jsonify({
            "error": "No PDF document found."
        }), 400

    pdf_file = pdf_files[-1]

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        pdf_file
    )

    try:

        reader = PdfReader(filepath)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        # Answer based on keywords

        if "eligibility" in question or "eligible" in question:

            answer = find_section(
                text,
                ["eligibility", "eligible", "qualification"]
            )

        elif "last date" in question or "deadline" in question:

            answer = find_section(
                text,
                ["last date", "deadline", "apply before"]
            )

        elif "duration" in question:

            answer = find_section(
                text,
                ["duration", "months", "weeks"]
            )

        elif "skill" in question or "skills" in question:

            answer = find_section(
                text,
                ["skills", "skill", "technical skills"]
            )

        elif "apply" in question or "application" in question:

            answer = find_section(
                text,
                ["apply", "application", "registration"]
            )

        elif "internship" in question:

            answer = text[:1000]

        else:

            answer = find_section(
                text,
                question.split()
            )

        return jsonify({

            "success": True,

            "answer": answer
        })

    except Exception as e:

        return jsonify({

            "error": str(e)

        }), 500


# RUN APPLICATION

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )