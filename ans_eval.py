import nltk
from nltk.corpus import wordnet
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

def preprocess_text(text):
    """
    Preprocess text by removing punctuation, converting to lowercase,
    removing stopwords, and lemmatizing words.
    """
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return tokens

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def calculate_similarity(answer, key):
    """
    Calculate semantic similarity between two texts using improved word-level matching.
    """
    # Preprocess both texts
    answer_tokens = preprocess_text(answer)
    key_tokens = preprocess_text(key)
    
    # Calculate matches
    score = 0
    matched_answer_tokens = set()
    
    for key_word in key_tokens:
        best_match_score = 0
        
        # Direct match
        if key_word in answer_tokens and key_word not in matched_answer_tokens:
            best_match_score = 1
            matched_answer_tokens.add(key_word)
        else:
            # Check synonyms
            key_synsets = wordnet.synsets(key_word)
            
            for answer_word in answer_tokens:
                if answer_word in matched_answer_tokens:
                    continue
                    
                answer_synsets = wordnet.synsets(answer_word)
                
                # Calculate maximum similarity between all synset combinations
                for key_syn in key_synsets:
                    for ans_syn in answer_synsets:
                        try:
                            similarity = key_syn.path_similarity(ans_syn)
                            if similarity and similarity > best_match_score:
                                best_match_score = similarity
                                matched_answer_tokens.add(answer_word)
                        except:
                            continue
        
        score += best_match_score
    
    return score / max(len(key_tokens), 1)

def evaluate_answers(answer_file_path, answer_key_file_path):
    """
    Compare the uploaded answer document with the answer key and generate a score.
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        student_answer = None
        answer_key = None

        # Read student answer file
        for encoding in encodings:
            try:
                with open(answer_file_path, 'r', encoding=encoding) as answer_file:
                    student_answer = answer_file.read().strip()
                break
            except UnicodeDecodeError:
                continue

        # Read answer key file
        for encoding in encodings:
            try:
                with open(answer_key_file_path, 'r', encoding=encoding) as key_file:
                    answer_key = key_file.read().strip()
                break
            except UnicodeDecodeError:
                continue

        if student_answer is None or answer_key is None:
            return {
                "status": "error",
                "message": "Could not decode the files with any supported encoding."
            }

        if not student_answer or not answer_key:
            return {
                "status": "error",
                "message": "One or both files are empty."
            }

        # Split into sentences
        student_answers = sent_tokenize(student_answer)
        key_answers = sent_tokenize(answer_key)

        # Calculate scores for each sentence
        total_score = 0
        details = []
        
        for i, (student_sentence, key_sentence) in enumerate(zip(student_answers, key_answers), start=1):
            similarity = calculate_similarity(student_sentence, key_sentence)
            total_score += similarity
            
            # Add detailed feedback
            score_percentage = similarity * 100
            if score_percentage >= 80:
                feedback = "Excellent match"
            elif score_percentage >= 60:
                feedback = "Good match"
            elif score_percentage >= 40:
                feedback = "Partial match"
            else:
                feedback = "Poor match"
                
            details.append(f"Question {i}:")
            details.append(f"Score: {score_percentage:.2f}% - {feedback}")
            details.append(f"Student Answer: {student_sentence}")
            details.append(f"Expected Answer: {key_sentence}")
            details.append("-" * 40)

        # Calculate overall score
        overall_score = (total_score / len(key_answers)) * 100

        return {
            "status": "success",
            "overall_score": overall_score,
            "details": details
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during evaluation: {str(e)}"
        }