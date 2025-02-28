# Student Assessment System

## Project Information
### Developers
- **Shoun Salaji** (2447248)
- **Yojit Shinde** (2447260)

### Guide
Dr. Sudhakar Tharuman  
Department of Computer Science  
CHRIST (Deemed to be University), Bengaluru-29

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Architecture](#architecture)
6. [Technology Stack](#technology-stack)
7. [Screenshots](#screenshots)
8. [Development Status](#development-status)
9. [SDG Alignment](#sdg-alignment)

## Overview
The Student Assessment System is an advanced grading solution designed to automate evaluation processes, detect plagiarism, and identify malpractice in academic submissions. It leverages machine learning, AI-based content analysis, and OCR for handwritten assignments to ensure academic integrity and streamline grading workflows.

## Features
- **Answer Verification**
  - Automated evaluation against predefined answer keys
  - Plagiarism detection
  - Malpractice identification

- **Assignment Verification**
  - Originality checking
  - Structure and format validation
  - Peer-to-peer copying detection

- **Advanced Analysis**
  - Online plagiarism detection
  - AI-generated content identification
  - Handwritten text OCR conversion

## Setup
### Prerequisites
- Python 3.8 or higher
- Google Cloud Platform account
- Internet connection for API access

### Installation Steps
1. **Clone Repository**
   ```bash
   git clone https://github.com/sho6000/Student-Assessment-Sys.git
   cd Student-Assessment-Sys
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Google Cloud Vision Setup**
   1. Create a Google Cloud Project
   2. Enable the Cloud Vision API
   3. Create a service account and download credentials
   4. Rename credentials to `key.json`
   5. Place in project root directory
   > Note: `key.json` is git-ignored for security

4. **Test Files Setup**
   - Create `test_files` directory structure:
     ```
     test_files/
     ├── assignments/
     ├── answer_sheets/
     └── sample_documents/
     ```
   > Note: test_files directory is git-ignored

## Usage
1. **Start Application**
   ```bash
   streamlit run app.py
   ```

2. **Available Operations**
   - Upload and verify answer sheets
   - Process assignments for plagiarism
   - Detect AI-generated content
   - Convert handwritten documents to text

## Architecture
### Frontend
- Streamlit-based web interface
- Intuitive user controls
- Real-time feedback

### Backend
- Plagiarism detection engine
- Malpractice detection module
- Answer key matching algorithms

### APIs and Services
- Google Cloud Vision for OCR
- Google Gemini for content analysis
- Custom ML models for verification

## Technology Stack
- **Core:** Python
- **Frontend:** Streamlit
- **APIs:**
  - Google Cloud Vision API
  - Google Gemini API

## Screenshots
### Home Screen
![Home Screen](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210249.png)

### Answer Verification
![Answer Verification](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210832.png)

### Assignment Verification
![Assignment Verification](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/Screenshot%202025-01-07%20210936.png)

### OCR Results
![OCR Screen](https://github.com/sho6000/Student-Assessment-Sys/blob/master/screenshots/WhatsApp%20Image%202025-01-07%20at%2022.29.37_6a3eddc3.jpg)

## Development Status
### In Progress
- OCR accuracy optimization
- Enhanced malpractice detection
- Refined AI content analysis

### Planned Features
- Multi-language support
- Batch processing capabilities
- Advanced analytics dashboard

## SDG Alignment
### SDG 4: Quality Education
- Fair and accurate assessments
- Transparent learning outcomes
- Enhanced educational integrity

### SDG 16: Peace, Justice, and Strong Institutions
- Academic integrity reinforcement
- Ethical practice promotion
- Transparent evaluation systems
