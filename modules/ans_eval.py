# Load English language model
import spacy
from difflib import SequenceMatcher
import re
import en_core_web_sm


#try:
#    nlp = spacy.load('en_core_web_sm')
#except OSError:
#    import subprocess
#    print("Downloading language model...")
#    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
#    nlp = spacy.load('en_core_web_sm')

nlp = en_core_web_sm.load()

def clean_text(text):
    """Clean text for comparison"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace and split into words
    words = text.split()
    # Remove common words that don't carry much meaning
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

def calculate_similarity(text1, text2):
    """Calculate similarity using multiple metrics"""
    # Clean texts
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)
    
    if not clean1 or not clean2:
        return 0
    
    # Get word sets
    words1 = set(clean1.split())
    words2 = set(clean2.split())
    
    # Calculate word overlap (Jaccard similarity)
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    word_sim = intersection / union if union > 0 else 0
    
    # Get sequence similarity
    seq_sim = SequenceMatcher(None, clean1, clean2).ratio()
    
    # Get spaCy semantic similarity
    doc1 = nlp(clean1)
    doc2 = nlp(clean2)
    semantic_sim = doc1.similarity(doc2)
    
    # Calculate length similarity
    len_ratio = min(len(clean1), len(clean2)) / max(len(clean1), len(clean2))
    
    # Weighted combination
    final_sim = (
        semantic_sim * 0.35 +  # Semantic meaning
        seq_sim * 0.35 +      # Sequence/structure
        word_sim * 0.2 +      # Word overlap
        len_ratio * 0.1       # Length similarity
    ) * 100
    
    # Adjust score based on length difference
    if len_ratio < 0.5:  # If lengths are very different
        final_sim *= 0.8  # Reduce score
    
    # Boost score for very similar texts
    if seq_sim > 0.9 and word_sim > 0.9:
        final_sim = min(100, final_sim * 1.2)
    
    return final_sim

def evaluate_answers(answer_file_path, answer_key_file_path):
    """Compare student answer with answer key and return similarity percentage"""
    try:
        # Read files
        try:
            with open(answer_file_path, 'r', encoding='utf-8') as f:
                student_answer = f.read().strip()
            with open(answer_key_file_path, 'r', encoding='utf-8') as f:
                answer_key = f.read().strip()
        except UnicodeDecodeError:
            with open(answer_file_path, 'r', encoding='latin-1') as f:
                student_answer = f.read().strip()
            with open(answer_key_file_path, 'r', encoding='latin-1') as f:
                answer_key = f.read().strip()

        if not student_answer or not answer_key:
            return {
                "status": "error",
                "message": "One or both files are empty"
            }

        # Calculate similarity
        similarity = calculate_similarity(student_answer, answer_key)

        return {
            "status": "success",
            "overall_score": similarity,
            "details": []
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during evaluation: {str(e)}"
        }