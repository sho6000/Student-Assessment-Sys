# Student Assessment System

### **Developed By:**
- **Shoun Salaji** (2447248)
- **Yojit Shinde** (2447260)

### **Guide:**
Dr. Sudhakar Tharuman  
Department of Computer Science  
CHRIST (Deemed to be University), Bengaluru-29  

---

## **Project Overview**
The Student Assessment System is an advanced grading solution designed to automate evaluation processes, detect plagiarism, and identify malpractice in academic submissions. It leverages machine learning, AI-based content analysis, and OCR for handwritten assignments to ensure academic integrity and streamline grading workflows.

### **Key Features**
- **Answer Verification:** Automates answer evaluation by comparing submissions with a predefined answer key, detecting plagiarism and malpractice.
- **Assignment Verification:** Checks assignment originality, structure, and formatting while detecting peer-to-peer copying.
- **Plagiarism Detection:** Uses APIs and algorithms for detecting online and peer plagiarism.
- **AI Content Detection:** Identifies AI-generated content in assignments to ensure originality.
- **OCR Integration:** Converts handwritten submissions into digital text for verification (currently under optimization).

---

## **System Architecture**
1. **Frontend:** Desktop-based application interface using Python Tkinter for educators.
2. **Backend:** 
   - Plagiarism detection engine with web scraping and machine learning.
   - Malpractice detection module for peer-to-peer comparison.
   - Answer key matching and scoring algorithms.
3. **Database:** PostgreSQL/MySQL for secure storage of submissions and results.

---

## **Screenshots**
### **1. Home Screen**
![Home Screen](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210249.png)

### **2. Answer Verification Module**
![Answer Verification](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210832.png)

### **3. Assignment Verification Module**
![Assignment Verification](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210936.png)

### **4. Results OCR Screen**
![OCR Screen](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/WhatsApp%20Image%202025-01-07%20at%2022.29.37_6a3eddc3.jpg)

---

## **Technology Stack**
- **Programming Language:** Python
- **Frontend Framework:** Tkinter
- **Database:** PostgreSQL/MySQL
- **APIs and Tools:**
  - Google Gemini API for plagiarism and AI content detection
  - Tesseract OCR for handwritten assignment conversion

---

## **Features in Progress**
- **OCR Optimization:** Improving accuracy for handwritten assignment verification.
- **Malpractice Detection:** Enhancing detection mechanisms for peer-to-peer content similarity.
- **Refined AI Content Analysis:** Expanding coverage for detecting AI-generated submissions.

---

## **Alignment with SDG Goals**
1. **SDG 4: Quality Education**
   - Promotes fair and accurate assessments.
   - Supports transparent learning outcomes.

2. **SDG 16: Peace, Justice, and Strong Institutions**
   - Reinforces academic integrity through ethical practices.

---

## **Installation**
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/student-assessment-system.git
