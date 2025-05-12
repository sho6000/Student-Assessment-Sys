import spacy
from difflib import SequenceMatcher
import re
import logging
import en_core_web_sm
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model
nlp = en_core_web_sm.load()

def preprocess_text(text):
    """
    Enhanced text preprocessing with better handling of document structure and domain-specific terminology
    """
    if not text:
        logger.warning("Empty text input")
        return ""
    
    # Convert to string (in case of non-string input)
    text = str(text)
    
    # Convert to lowercase before any processing
    text = text.lower()
    
    # Preserve sentence structure for better analysis
    # Remove non-alphanumeric except for sentence punctuation
    text = re.sub(r'[^\w\s.,;:!?-]', '', text)
    
    # Remove bullet points and common formatting artifacts
    text = re.sub(r'●|○|\*|\d+\.\s', '', text)
    
    # Process document in sentences to maintain context
    doc = nlp(text)
    processed_sentences = []
    
    for sent in doc.sents:
        # Filter out stop words for each sentence but preserve important domain-specific terms
        filtered_tokens = [token.text for token in sent 
                          if (not token.is_stop or token.text in ['not', 'no', 'never', 'cannot']) 
                          and not token.is_punct and len(token.text) > 1]
        if filtered_tokens:
            processed_sentences.append(' '.join(filtered_tokens))
    
    # If all content was filtered out, fall back to basic processing
    if not processed_sentences:
        # Basic fallback preprocessing
        words = [word for word in text.split() if len(word) > 1]
        stop_words = set(nlp.Defaults.stop_words) - {'not', 'no', 'never', 'cannot'}  # Preserve negations
        words = [word for word in words if word not in stop_words]
        return ' '.join(words)
    
    return ' '.join(processed_sentences)

def extract_key_concepts(text):
    """
    Extract meaningful key concepts from text using NLP with improved domain awareness
    """
    doc = nlp(text)
    
    # Extract nouns, proper nouns, verbs, and adjectives as key concepts
    concepts = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"] and not token.is_stop and len(token.text) > 1:
            concepts.append(token.lemma_.lower())
    
    # Also extract noun phrases and entity mentions
    for chunk in doc.noun_chunks:
        # Clean up the noun phrase
        clean_chunk = re.sub(r'[^\w\s]', '', chunk.text).lower().strip()
        if clean_chunk and len(clean_chunk) > 3:  # Ensure meaningful phrases
            concepts.append(clean_chunk)
    
    # Add named entities as important concepts
    for ent in doc.ents:
        clean_ent = re.sub(r'[^\w\s]', '', ent.text).lower().strip()
        if clean_ent and len(clean_ent) > 1:
            concepts.append(clean_ent)
    
    return concepts

def calculate_content_overlap(text1, text2):
    """
    Calculate meaningful content overlap between documents using key concepts
    """
    # Extract key concepts
    concepts1 = extract_key_concepts(text1)
    concepts2 = extract_key_concepts(text2)
    
    # Create frequency counters
    counter1 = Counter(concepts1)
    counter2 = Counter(concepts2)
    
    # Calculate cosine similarity between concept frequency vectors
    shared_concepts = set(counter1.keys()) & set(counter2.keys())
    
    if not shared_concepts:
        return 0.0
    
    # Calculate vector magnitudes
    magnitude1 = sum(counter1[concept]**2 for concept in counter1)
    magnitude2 = sum(counter2[concept]**2 for concept in counter2)
    
    # Calculate dot product
    dot_product = sum(counter1[concept] * counter2[concept] for concept in shared_concepts)
    
    # Cosine similarity
    if magnitude1 * magnitude2 == 0:
        return 0.0
    
    return dot_product / ((magnitude1 * magnitude2) ** 0.5)

def calculate_tfidf_similarity(text1, text2):
    """
    Calculate TF-IDF based cosine similarity between texts
    This helps identify important terms and their relative importance
    """
    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(min_df=1, stop_words='english')
        
        # Fit and transform the texts
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return similarity
    except Exception as e:
        logger.error(f"Error in TF-IDF similarity calculation: {e}")
        return 0.0

def calculate_embedding_similarity(text1, text2):
    """
    Calculate semantic similarity using word embeddings
    This captures deeper semantic relationships between texts
    """
    try:
        # Process texts with spaCy
        doc1 = nlp(text1[:5000])  # Limit text length to prevent memory issues
        doc2 = nlp(text2[:5000])
        
        # If documents are empty after processing, return 0
        if len(doc1) == 0 or len(doc2) == 0:
            return 0.0
        
        # Calculate vector similarity
        similarity = doc1.similarity(doc2)
        
        # Normalize to ensure it's between 0 and 1
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        logger.error(f"Error in embedding similarity calculation: {e}")
        return 0.0

def detect_key_phrase_matches(text1, text2):
    """
    Detect matches of important phrases between texts
    """
    # Extract sentences
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    
    sentences1 = [sent.text.lower() for sent in doc1.sents]
    sentences2 = [sent.text.lower() for sent in doc2.sents]
    
    # Extract noun phrases
    phrases1 = [chunk.text.lower() for chunk in doc1.noun_chunks if len(chunk.text) > 5]
    phrases2 = [chunk.text.lower() for chunk in doc2.noun_chunks if len(chunk.text) > 5]
    
    # Calculate phrase match ratio
    matched_phrases = 0
    for phrase1 in phrases1:
        for phrase2 in phrases2:
            if SequenceMatcher(None, phrase1, phrase2).ratio() > 0.8:
                matched_phrases += 1
                break
    
    # Calculate sentence similarity
    sentence_similarities = []
    for sent1 in sentences1:
        for sent2 in sentences2:
            similarity = SequenceMatcher(None, sent1, sent2).ratio()
            if similarity > 0.6:  # Only consider reasonably similar sentences
                sentence_similarities.append(similarity)
    
    # Calculate average sentence similarity
    avg_sentence_sim = sum(sentence_similarities) / len(sentence_similarities) if sentence_similarities else 0
    
    # Calculate phrase match ratio
    phrase_match_ratio = matched_phrases / len(phrases1) if phrases1 else 0
    
    return (avg_sentence_sim + phrase_match_ratio) / 2

def detect_document_structure(text):
    """
    Detect document structure features to compare document types
    """
    features = {
        "bullet_points": len(re.findall(r'●|○|\*|\d+\.\s', text)),
        "has_sections": bool(re.search(r'\n\s*[A-Z][^.]*:', text)),
        "avg_sentence_length": 0,
        "avg_paragraph_length": 0
    }
    
    # Calculate average sentence length
    doc = nlp(text)
    sentences = list(doc.sents)
    if sentences:
        features["avg_sentence_length"] = sum(len(sent) for sent in sentences) / len(sentences)
    
    # Calculate average paragraph length
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if paragraphs:
        features["avg_paragraph_length"] = sum(len(p) for p in paragraphs) / len(paragraphs)
    
    return features

def structural_similarity(text1, text2):
    """
    Compare structural features of documents
    """
    features1 = detect_document_structure(text1)
    features2 = detect_document_structure(text2)
    
    # Compare structural features
    bullet_similarity = 1.0 if features1["bullet_points"] > 0 and features2["bullet_points"] > 0 else 0.0
    section_similarity = 1.0 if features1["has_sections"] == features2["has_sections"] else 0.0
    
    # Compare sentence and paragraph length patterns (normalized difference)
    sent_len_diff = abs(features1["avg_sentence_length"] - features2["avg_sentence_length"])
    sent_len_sim = max(0, 1.0 - (sent_len_diff / max(features1["avg_sentence_length"], features2["avg_sentence_length"], 1)))
    
    para_len_diff = abs(features1["avg_paragraph_length"] - features2["avg_paragraph_length"])
    para_len_sim = max(0, 1.0 - (para_len_diff / max(features1["avg_paragraph_length"], features2["avg_paragraph_length"], 1)))
    
    # Weight structural similarities
    return (bullet_similarity * 0.3 + section_similarity * 0.3 + sent_len_sim * 0.2 + para_len_sim * 0.2)

def calculate_similarity(text1, text2):
    """
    Improved similarity calculation with enhanced semantic understanding
    """
    # Initial validation - check if texts are significantly different in length
    len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2)) if max(len(text1), len(text2)) > 0 else 0
    if len_ratio < 0.2:  # If one text is less than 20% the length of the other
        logger.info("Texts have very different lengths, likely not similar")
        
    # Preprocess texts
    processed1 = preprocess_text(text1)
    processed2 = preprocess_text(text2)
    
    # Logging for debugging
    logger.info(f"Processed Text 1: {processed1[:100]}...")
    logger.info(f"Processed Text 2: {processed2[:100]}...")
    
    # Check if texts are too short after processing
    if len(processed1) < 10 or len(processed2) < 10:
        logger.warning("Texts too short after processing")
        return 0
    
    try:
        # Method 1: Content-based overlap
        content_sim = calculate_content_overlap(text1, text2)
        logger.info(f"Content-based Similarity: {content_sim:.2f}")
        
        # Method 2: Semantic similarity with spaCy
        semantic_sim = calculate_embedding_similarity(processed1, processed2)
        logger.info(f"Semantic Similarity: {semantic_sim:.2f}")
        
        # Method 3: TF-IDF based similarity
        tfidf_sim = calculate_tfidf_similarity(processed1, processed2)
        logger.info(f"TF-IDF Similarity: {tfidf_sim:.2f}")
        
        # Method 4: Key phrase matching
        phrase_sim = detect_key_phrase_matches(text1, text2)
        logger.info(f"Key Phrase Similarity: {phrase_sim:.2f}")
        
        # Method 5: Structural similarity
        struct_sim = structural_similarity(text1, text2)
        logger.info(f"Structural Similarity: {struct_sim:.2f}")
        
        # Method 6: Sequential similarity as final check
        seq_sim = SequenceMatcher(None, processed1, processed2).ratio()
        logger.info(f"Sequence Similarity: {seq_sim:.2f}")
        
        # Calculate semantic boost factor
        # If semantic similarity is high but content overlap is lower, boost the score
        semantic_boost = 1.0
        if semantic_sim > 0.7 and content_sim < 0.5:
            semantic_boost = 1.3  # 30% boost for semantically similar content
            logger.info("Applied semantic similarity boost")
        
        # High penalty for very low content and semantic overlap
        if content_sim < 0.05 and semantic_sim < 0.2:
            logger.info("Very low content and semantic overlap detected")
            penalty_factor = 0.3
        else:
            penalty_factor = 1.0
        
        # Weighted combination with semantic similarity having higher weight
        final_sim = penalty_factor * semantic_boost * (
            content_sim * 0.25 +       # Content overlap
            semantic_sim * 0.30 +      # Semantic similarity (increased weight)
            tfidf_sim * 0.20 +         # TF-IDF similarity
            phrase_sim * 0.15 +        # Key phrase matching
            struct_sim * 0.05 +        # Document structure
            seq_sim * 0.05             # Sequence matching
        ) * 100
        
        # Apply progressive scoring curve to reward higher similarity
        # This gives higher scores to answers that are more semantically similar
        if final_sim > 60:
            final_sim = 60 + (final_sim - 60) * 1.2  # Boost scores above 60%
        
        # Threshold for minimum similarity
        if content_sim < 0.02 and semantic_sim < 0.2:
            logger.info("Content and semantic similarity both very low")
            final_sim = min(final_sim, 10)  # Cap at max 10% for very different docs
        
    except Exception as e:
        logger.error(f"Error in similarity calculation: {e}")
        return 0
    
    # Constrain to 0-100 range
    return max(0, min(100, final_sim))

def evaluate_answers(answer_file_path, answer_key_file_path):
    """
    Enhanced answer evaluation with improved encoding detection and validation
    """
    # Possible encodings to try
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    student_answer = None
    answer_key = None
    
    # Try to read files with different encodings
    for encoding in encodings:
        try:
            if not student_answer:
                with open(answer_file_path, 'r', encoding=encoding) as f:
                    student_answer = f.read().strip()
            
            if not answer_key:
                with open(answer_key_file_path, 'r', encoding=encoding) as f:
                    answer_key = f.read().strip()
            
            if student_answer and answer_key:
                break
                
        except Exception as e:
            logger.warning(f"Failed with {encoding} encoding: {e}")
    
    # Validate successful file reading
    if not student_answer or not answer_key:
        return {
            "status": "error",
            "message": "Could not read files with any known encoding"
        }
    
    # Basic content validation
    if len(student_answer) < 10 or len(answer_key) < 10:
        return {
            "status": "error", 
            "message": "One or both files contain insufficient content",
            "overall_score": 0
        }
    
    # Calculate similarity
    similarity = calculate_similarity(student_answer, answer_key)
    
    # Additional quality checks
    similarity_categories = {
        "very_low": similarity < 15,
        "low": 15 <= similarity < 30,
        "moderate": 30 <= similarity < 60,
        "high": 60 <= similarity < 85,
        "very_high": similarity >= 85
    }
    
    category = next(cat for cat, condition in similarity_categories.items() if condition)
    
    return {
        "status": "success",
        "overall_score": similarity,
        "similarity_category": category,
        "details": [
            f"Similarity Score: {similarity:.2f}%",
            f"Content Words in Student Answer: {len(preprocess_text(student_answer).split())}",
            f"Content Words in Answer Key: {len(preprocess_text(answer_key).split())}"
        ]
    }

# Example usage
if __name__ == "__main__":
    # Test with sample paths
    student_path = "student_answer.txt"
    key_path = "answer_key.txt"
    result = evaluate_answers(student_path, key_path)
    print(result)