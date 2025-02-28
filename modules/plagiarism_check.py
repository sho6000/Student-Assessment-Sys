import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2

load_dotenv()

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
            content = ""
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
            else:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

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