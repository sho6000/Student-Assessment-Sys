import os
from google.cloud import vision
from pdf2image import convert_from_path
import tempfile
import io
from PIL import Image

# Initialize the Google Cloud Vision client
client = vision.ImageAnnotatorClient.from_service_account_json('key.json')

def perform_ocr(file_path, log_callback=None):
    """Perform OCR using Google Cloud Vision API"""
    try:
        if log_callback:
            log_callback("Starting OCR processing...\n")

        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle PDF files
        if file_ext == '.pdf':
            if log_callback:
                log_callback("Converting PDF to images...\n")
            
            try:
                # Convert PDF to images
                with tempfile.TemporaryDirectory() as temp_dir:
                    images = convert_from_path(file_path)
                    text = ""
                    
                    for i, image in enumerate(images):
                        if log_callback:
                            log_callback(f"Processing page {i+1}...\n")
                        
                        # Convert PIL Image to bytes
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        content = img_byte_arr.getvalue()
                        
                        # Create vision image object
                        image = vision.Image(content=content)
                        
                        # Perform OCR
                        response = client.document_text_detection(image=image)
                        if response.error.message:
                            raise Exception(response.error.message)
                            
                        text += response.full_text_annotation.text + "\n\n"
                    
                    return text.strip(), None
                    
            except Exception as e:
                return None, f"PDF processing error: {str(e)}"
        
        # Handle image files
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            if log_callback:
                log_callback("Processing image...\n")
            
            try:
                # Read image file
                with open(file_path, 'rb') as image_file:
                    content = image_file.read()
                
                # Create vision image object
                image = vision.Image(content=content)
                
                # Perform OCR
                response = client.document_text_detection(image=image)
                if response.error.message:
                    raise Exception(response.error.message)
                
                return response.full_text_annotation.text.strip(), None
                
            except Exception as e:
                return None, f"Image processing error: {str(e)}"
            
        else:
            return None, f"Unsupported file format: {file_ext}"
            
    except Exception as e:
        return None, f"Error during OCR: {str(e)}"

def save_ocr_result(text, output_path):
    """Save OCR result to file with UTF-8 encoding"""
    try:
        # Ensure the text is properly encoded
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        # Write with UTF-8 encoding and BOM for Windows compatibility
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error saving OCR result: {str(e)}")
        return False