import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2
import docx

load_dotenv()

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    content = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
    return content

def extract_text_from_docx(file_path):
    """
    Extracts text from a Word document using python-docx.
    """
    content = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            content += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from Word document {file_path}: {e}")
    return content

def extract_text(file_path):
    """
    Extracts text from a file based on its extension.
    Supports PDF, DOCX, and plain text files.
    """
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        # Assume it's a plain text file
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

def check_plagiarism(file_paths):
    """
    Checks for potential plagiarism using Gemini API.
    Returns a simple summary for each file.
    """
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    results = {}

    for file_path in file_paths:
        try:
            content = extract_text(file_path)

            if not content.strip():
                raise ValueError("No text content could be extracted from the file")

            prompt = f"""Analyze this text for plagiarism and provide a brief summary including:
            1. An estimated plagiarism percentage
            2. Potential sources if plagiarism is detected
            
            Keep the response concise and direct.
            
            Text to analyze:
            {content}"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            results[file_path] = response_text.strip()

        except Exception as e:
            results[file_path] = f"Error analyzing file: {str(e)}"

    return results