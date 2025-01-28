import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image
import os

# For Windows, you need to set the Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    """
    Preprocess the image to improve OCR accuracy for handwritten text.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Noise removal using median blur
    denoised = cv2.medianBlur(thresh, 3)
    
    # Dilation to connect text components
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(denoised, kernel, iterations=1)
    
    # Invert back
    final = cv2.bitwise_not(dilated)
    
    return final

def perform_ocr(file_path, log_callback=None):
    """
    Perform OCR on the given file (image or PDF).
    Returns the extracted text and any error message.
    """
    try:
        # Set Tesseract path
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Check if file is PDF
        if file_path.lower().endswith('.pdf'):
            try:
                # Use raw string and normalize path
                poppler_path = os.path.normpath(r"C:\Program Files\Popper\poppler-24.08.0\Library\bin")
                if log_callback:
                    log_callback(f"Using Poppler path: {poppler_path}\n")
                
                # Convert using normalized paths
                images = pdf2image.convert_from_path(
                    os.path.normpath(file_path),
                    poppler_path=poppler_path
                )
                
                text_results = []
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(image)
                    text_results.append(text)
                
                # Create output filename using normalized path
                output_path = os.path.normpath(os.path.splitext(file_path)[0] + "_ocr.txt")
                final_text = '\n\n'.join(text_results)
                
                # Save the results
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_text)
                
                return final_text, None
                
            except Exception as e:
                detailed_error = f"PDF conversion failed: {str(e)}\nMake sure Poppler is installed and the path is correct."
                return None, detailed_error
        
        else:  # Handle image files
            # Read image
            img = cv2.imread(file_path)
            if img is None:
                return None, "Error: Unable to read image file"
            
            # Preprocess image
            processed_img = preprocess_image(img)
            
            # Perform OCR with optimized configuration
            text = pytesseract.image_to_string(
                processed_img,
                config='--psm 6 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?()-:;% "'
            )
            
            return text, None
            
    except Exception as e:
        return None, f"Error during OCR: {str(e)}"

def save_ocr_result(text, output_path):
    """
    Save the OCR result to a text file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        return False
