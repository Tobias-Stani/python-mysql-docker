from flask import Flask, request, render_template, redirect, url_for
import fitz  # PyMuPDF
import os
import shutil
from transformers import pipeline

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Cargar el modelo de resumen de Hugging Face
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text

def summarize_text(text):
    if len(text) > 1000:
        summary = summarizer(text[:1000], max_length=150, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    return "El texto es demasiado corto para resumir."

@app.route("/", methods=["GET", "POST"])
def upload_pdf():
    extracted_text = None
    summary_text = None
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        extracted_text = extract_text_from_pdf(file_path)
        summary_text = summarize_text(extracted_text)
    return render_template("index.html", text=extracted_text, summary=summary_text)

if __name__ == "__main__":
    app.run(debug=True)
