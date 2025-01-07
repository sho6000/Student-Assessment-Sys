import os
import PyPDF2
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

def compare_files(file_paths):
    """
    Compares the uploaded files for similarity using Cosine Similarity (TF-IDF).
    Compares each pair of files and returns a similarity score.
    """
    texts = []
    
    # Extract text from each PDF file
    for file_path in file_paths:
        texts.append(extract_text_from_pdf(file_path))
    
    # Create a TF-IDF Vectorizer and transform the documents into vectors
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Calculate cosine similarity between the documents
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    # Store results in a dictionary
    similarity_results = {}
    for i, file1 in enumerate(file_paths):
        for j, file2 in enumerate(file_paths):
            if i < j:  # Avoid duplicate comparisons
                similarity_results[(file_paths[i], file_paths[j])] = cosine_sim[i][j-1]
    
    return similarity_results
