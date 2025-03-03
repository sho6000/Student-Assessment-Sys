import cv2
import numpy as np
from imutils.perspective import four_point_transform
from imutils import contours
import imutils

class OMRProcessor:
    def __init__(self, answer_key=None, questions_count=None, options_count=None):
        """Initialize OMR processor with optional answer key and configurable parameters"""
        self.answer_key = answer_key
        self.questions_count = questions_count
        self.options_count = options_count
        self.is_configured = False

    def configure(self, questions_count, options_count):
        """Configure the processor with question and option counts"""
        self.questions_count = questions_count
        self.options_count = options_count
        self.is_configured = True
        return True

    def preprocess_image(self, image):
        """Step 1 & 2: Detect exam and apply perspective transform"""
        # Convert to grayscale and blur
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edged = cv2.Canny(blurred, 75, 200)
        
        # Find contours
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        doc_cnt = None

        # Ensure at least one contour was found
        if len(cnts) > 0:
            # Sort contours by size
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            
            # Loop over contours
            for c in cnts:
                # Approximate the contour
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                
                # If we have found a contour with four points, we can break
                if len(approx) == 4:
                    doc_cnt = approx
                    break

        # Apply perspective transform
        if doc_cnt is not None:
            paper = four_point_transform(image, doc_cnt.reshape(4, 2))
            warped = four_point_transform(gray, doc_cnt.reshape(4, 2))
            return paper, warped
        return None, None

    def extract_bubbles(self, warped):
        """Step 3: Extract bubbles from the warped image"""
        # Apply threshold
        thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Find contours
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        # Filter bubble-like contours
        bubble_cnts = []
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            aspect_ratio = w / float(h)
            
            # Check if the contour has bubble-like properties
            if w >= 20 and h >= 20 and aspect_ratio >= 0.9 and aspect_ratio <= 1.1:
                bubble_cnts.append(c)
        
        return bubble_cnts

    def sort_bubbles(self, bubble_cnts):
        """Step 4: Sort bubbles into rows"""
        if not self.is_configured:
            return []

        # Sort bubbles by y-coordinate (question rows)
        question_rows = []
        y_coords = {}
        
        for c in bubble_cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            cy = y + (h // 2)
            
            # Group bubbles with similar y-coordinates (within 10 pixels)
            matched = False
            for key in y_coords.keys():
                if abs(cy - key) < 10:
                    y_coords[key].append((x, cy, c))
                    matched = True
                    break
            
            if not matched:
                y_coords[cy] = [(x, cy, c)]
        
        # Sort rows by y-coordinate and bubbles within rows by x-coordinate
        for y in sorted(y_coords.keys()):
            row = sorted(y_coords[y], key=lambda x: x[0])
            if len(row) == self.options_count:  # Only include rows with correct number of options
                question_rows.append([c for (_, _, c) in row])
        
        return question_rows[:self.questions_count]  # Limit to configured number of questions

    def get_marked_answers(self, thresh, question_rows):
        """Step 5: Determine marked answers"""
        marked_answers = []
        
        for row in question_rows:
            bubble_scores = []
            
            for bubble in row:
                mask = np.zeros(thresh.shape, dtype="uint8")
                cv2.drawContours(mask, [bubble], -1, 255, -1)
                
                # Count non-zero pixels in the bubble area
                mask_pixels = cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask))
                bubble_scores.append(mask_pixels)
            
            # Get the index of the bubble with the highest score
            max_score = max(bubble_scores)
            if max_score > thresh.shape[0] * 0.1:  # Minimum threshold to consider a bubble marked
                marked_answers.append(bubble_scores.index(max_score))
            else:
                marked_answers.append(-1)  # No answer marked
        
        return marked_answers

    def grade_exam(self, image_data):
        """Process and grade an exam"""
        if not self.is_configured:
            return {
                "status": "error",
                "message": "OMR processor not configured. Please set number of questions and options first."
            }

        # Convert image data to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Apply preprocessing
        paper, warped = self.preprocess_image(image)
        if paper is None or warped is None:
            return {
                "status": "error",
                "message": "Could not detect exam paper in image"
            }
        
        # Extract and sort bubbles
        bubble_cnts = self.extract_bubbles(warped)
        question_rows = self.sort_bubbles(bubble_cnts)
        
        if not question_rows:
            return {
                "status": "error",
                "message": "Could not detect answer bubbles"
            }
        
        if len(question_rows) < self.questions_count:
            return {
                "status": "error",
                "message": f"Expected {self.questions_count} questions but found only {len(question_rows)}"
            }
        
        # Get threshold for marked answer detection
        thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Get marked answers
        marked_answers = self.get_marked_answers(thresh, question_rows)
        
        return {
            "status": "success",
            "total_questions": len(marked_answers),
            "marked_answers": marked_answers,
            "processed_image": paper
        }

    def process_answer_key(self, image_data):
        """Process answer key image and store correct answers"""
        result = self.grade_exam(image_data)
        if result["status"] == "success":
            self.answer_key = result["marked_answers"]
            return True
        return False

    def evaluate_answer_sheet(self, image_data):
        """Evaluate a student's answer sheet against the answer key"""
        if self.answer_key is None:
            return {
                "status": "error",
                "message": "Answer key not set"
            }
        
        result = self.grade_exam(image_data)
        if result["status"] != "success":
            return result
        
        # Compare with answer key
        correct_answers = 0
        total_questions = min(len(self.answer_key), len(result["marked_answers"]))
        
        for i in range(total_questions):
            if result["marked_answers"][i] == self.answer_key[i]:
                correct_answers += 1
        
        score = (correct_answers / total_questions) * 100
        
        return {
            "status": "success",
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score": score,
            "marked_answers": result["marked_answers"],
            "correct_answers_key": self.answer_key
        } 