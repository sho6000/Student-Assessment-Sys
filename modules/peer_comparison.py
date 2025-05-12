import os
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Function to extract text from PDF files
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

# Function to extract text from Word documents
def extract_text_from_docx(docx_path):
    """
    Extracts text from a Word document using python-docx.
    """
    text = ""
    try:
        doc = docx.Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from {docx_path}: {e}")
    return text

# Function to extract text from any supported file type
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
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

def compare_files(file_paths):
    """
    Compares the uploaded files for similarity using Cosine Similarity (TF-IDF).
    Compares each pair of files and returns a similarity score.
    """
    if len(file_paths) < 2:
        raise ValueError("At least two files are required for comparison.")
    
    texts = []
    
    # Extract text from each file
    for file_path in file_paths:
        texts.append(extract_text(file_path))
    
    # Create a TF-IDF Vectorizer and transform the documents into vectors
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Calculate pairwise cosine similarity for all files
    cosine_sim = cosine_similarity(tfidf_matrix)
    
    # Store results in a dictionary
    similarity_results = {}
    for i, file1 in enumerate(file_paths):
        for j, file2 in enumerate(file_paths):
            if i < j:  # Avoid duplicate and self-comparisons
                similarity_results[(file1, file2)] = cosine_sim[i][j]
    
    return similarity_results
