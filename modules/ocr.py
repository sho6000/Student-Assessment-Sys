import requests
import base64
import os

def perform_ocr(file_path, log_callback=None):
    """Perform OCR using RapidAPI's handwriting recognition service"""
    try:
        # Read the image file as binary
        with open(file_path, 'rb') as file:
            image_data = file.read()
        
        # Convert image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        url = "https://pen-to-print-handwriting-ocr.p.rapidapi.com/recognize/"
        
        # Prepare the payload
        payload = {
            "imageBase64": base64_image,
            "includeSubScan": "0",
            "Session": "string"
        }
        
        # API headers
        headers = {
            "x-rapidapi-key": "161093014amsh6516ff8df6a5904p14c013jsnb056e3345b2d",
            "x-rapidapi-host": "pen-to-print-handwriting-ocr.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        if log_callback:
            log_callback("Sending image for OCR processing...\n")
        
        # Make API request
        response = requests.post(url, data=payload, headers=headers)
        result = response.json()
        
        if 'text' in result:
            return result['text'], None
        else:
            return None, "OCR failed to extract text"
            
    except Exception as e:
        return None, f"Error during OCR: {str(e)}"

def save_ocr_result(text, output_path):
    """Save OCR result to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception:
        return False