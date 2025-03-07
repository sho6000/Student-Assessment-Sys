from dotenv import load_dotenv
import google.generativeai as genai
import os
import PyPDF2

load_dotenv()

def detect_ai_content(file_paths):
    """
    Detects the percentage of AI-generated content in uploaded files using Gemini API.
    :param file_paths: List of file paths for the uploaded files.
    :return: Dictionary containing file names and AI detection results with percentages.
    """
    # Initialize Gemini API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Store your API key in environment variables
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    results = {}

    for file_path in file_paths:
        try:
            content = ""
            # Check if file is PDF
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
            else:
                # For text files, use regular text reading
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

            if not content.strip():
                raise ValueError("No text content could be extracted from the file")

            # Prompt for Gemini to analyze the content
            prompt = f"""Analyze the following text and determine the likelihood (as a percentage) 
            that it was generated by AI. Provide only the percentage number in your response.
            
            Text to analyze:
            {content}"""

            # Get response from Gemini
            response = model.generate_content(prompt)
            
            # Extract percentage from response, ensuring we handle the response text properly
            response_text = response.text if hasattr(response, 'text') else str(response)
            ai_percentage = response_text.strip().rstrip('%')
            
            try:
                percentage = float(ai_percentage)
            except ValueError:
                percentage = 0.0  # Default value if parsing fails
            
            # Store result with more detailed information
            results[file_path] = {
                "ai_percentage": percentage,
                "status": "success",
                "content_length": len(content)
            }

        except Exception as e:
            results[file_path] = {
                "ai_percentage": None,
                "status": "error",
                "error_message": str(e)
            }

    return results