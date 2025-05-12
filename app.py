import streamlit as st
import os
from modules.peer_comparison import compare_files
from modules.plagiarism_check import check_plagiarism
from modules.ai_content import detect_ai_content
from modules.ocr import perform_ocr, save_ocr_result
from modules.ans_eval import evaluate_answers
from modules.omr_processor import OMRProcessor
from fpdf import FPDF
import io
from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from streamlit_lottie import st_lottie
import json
import time

# Initialize session states
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = {}
if 'last_files_count' not in st.session_state:
    st.session_state.last_files_count = 0
if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = {
        'peer_comparison': False,
        'plagiarism_check': False,
        'ai_detection': False
    }
if 'omr_processor' not in st.session_state:
    st.session_state.omr_processor = OMRProcessor()

def reset_checkboxes():
    """Reset all checkboxes to unchecked state"""
    st.session_state.checkboxes = {
        'peer_comparison': False,
        'plagiarism_check': False,
        'ai_detection': False
    }

def reset_peer_comparison():
    """Reset only the peer comparison checkbox"""
    st.session_state.checkboxes['peer_comparison'] = False

def clear_ocr_results():
    """Clear OCR results from session state"""
    st.session_state.ocr_results = {}

def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = {'.jpg', '.jpeg', '.png'}
    return os.path.splitext(filename.lower())[1] in image_extensions

def has_unprocessed_images(files):
    """Check for unprocessed image files"""
    return any(is_image_file(file.name) for file in files 
              if file.name not in st.session_state.ocr_results)

def process_ocr(file, progress_callback=None):
    """Process a single file through OCR"""
    temp_file = f"temp_{file.name}"
    try:
        with open(temp_file, "wb") as f:
            f.write(file.getbuffer())
        return perform_ocr(temp_file, progress_callback)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

class PDF(FPDF):
    def header(self):
        # Add logo or header image if needed
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Student Assessment System - Analysis Report', 0, 1, 'C')
        self.ln(10)

def generate_pdf_report(results_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add timestamp
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
    pdf.ln(5)

    # Add content for each section
    for section in results_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, section['title'], 0, 1)
        
        pdf.set_font('Arial', '', 11)
        for result in section['content']:
            # Handle potential encoding issues by replacing problematic characters
            clean_text = result.encode('latin-1', errors='replace').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
        pdf.ln(5)

    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # If encoding fails, try with a more robust approach
        buffer = io.BytesIO()
        pdf.output(buffer)
        return buffer.getvalue()

def generate_peer_comparison(temp_files):
    """Generate peer comparison section for the report"""
    peer_results = []
    results = compare_files(temp_files)
    
    for files, similarity in results.items():
        if len(files) == 2:
            file1, file2 = files
            similarity_percentage = similarity * 100
            peer_results.append(
                f"Comparing {os.path.basename(file1)} with {os.path.basename(file2)}\n"
                f"Similarity Score: {similarity_percentage:.1f}%\n"
            )
            
            # Display results in UI
            st.markdown("---")
            st.markdown("### 📄 Similarity Results")
            col1, col2 = st.columns(2)
            with col1:
                st.write("📄 File 1:", os.path.basename(file1))
                st.write("📄 File 2:", os.path.basename(file2))
            with col2:
                st.metric(
                    "Similarity Score",
                    f"{similarity_percentage:.1f}%",
                    delta=None
                )
    
    if peer_results:
        return [{
            'title': 'Peer-to-Peer Comparison Results',
            'content': peer_results
        }]
    return []

def generate_plagiarism_check(temp_files):
    """Generate plagiarism check section for the report"""
    plagiarism_results_list = []
    st.markdown("### 🔍 Plagiarism Check Results")
    
    plagiarism_results = check_plagiarism(temp_files)
    for file_path, result in plagiarism_results.items():
        st.markdown(f"**File: {os.path.basename(file_path)}**")
        st.info(result)
        plagiarism_results_list.append(
            f"File: {os.path.basename(file_path)}\n{result}\n"
        )
    
    if plagiarism_results_list:
        return [{
            'title': 'Plagiarism Check Results',
            'content': plagiarism_results_list
        }]
    return []

def generate_ai_detection(temp_files):
    """Generate AI detection section for the report"""
    ai_results_list = []
    st.markdown("### 🤖 AI Content Detection Results")
    
    ai_results = detect_ai_content(temp_files)
    for file_path, result in ai_results.items():
        filename = os.path.basename(file_path)
        if result['status'] == 'success':
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{filename}**")
            with col2:
                st.metric(
                    "AI Content Probability",
                    f"{result['ai_percentage']}%"
                )
            st.write(f"Content Length: {result['content_length']} characters")
            
            ai_results_list.append(
                f"File: {filename}\n"
                f"AI Content Probability: {result['ai_percentage']}%\n"
                f"Content Length: {result['content_length']} characters\n"
            )
        else:
            st.error(f"{filename}: Error - {result['error_message']}")
            ai_results_list.append(
                f"File: {filename}\nError: {result['error_message']}\n"
            )
    
    if ai_results_list:
        return [{
            'title': 'AI Content Detection Results',
            'content': ai_results_list
        }]
    return []

def process_omr(answer_sheet, correct_sheet):
    """Process OMR sheets and return marks"""
    try:
        # Read the images
        answer_img = cv2.imdecode(np.frombuffer(answer_sheet.read(), np.uint8), cv2.IMREAD_COLOR)
        correct_img = cv2.imdecode(np.frombuffer(correct_sheet.read(), np.uint8), cv2.IMREAD_COLOR)
        
        # Reset file pointers
        answer_sheet.seek(0)
        correct_sheet.seek(0)
        
        # Convert to grayscale
        answer_gray = cv2.cvtColor(answer_img, cv2.COLOR_BGR2GRAY)
        correct_gray = cv2.cvtColor(correct_img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, answer_thresh = cv2.threshold(answer_gray, 127, 255, cv2.THRESH_BINARY)
        _, correct_thresh = cv2.threshold(correct_gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours (bubbles)
        answer_contours, _ = cv2.findContours(answer_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        correct_contours, _ = cv2.findContours(correct_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Compare marked answers with correct answers
        total_questions = len(correct_contours)
        correct_answers = 0
        
        for ans_contour, corr_contour in zip(answer_contours, correct_contours):
            # Calculate overlap
            if cv2.matchShapes(ans_contour, corr_contour, cv2.CONTOURS_MATCH_I1, 0.0) < 0.1:
                correct_answers += 1
        
        # Calculate score
        score = (correct_answers / total_questions) * 100
        return {
            "status": "success",
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score": score
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def main():
    st.set_page_config(
        page_title="Student Assessment System",
        page_icon="assets/pen.jpg",
        layout="wide"
    )

    # # ✅ Create a placeholder for the loading animation
    # placeholder = st.empty()

    # # ✅ Load Lottie animation from a local JSON file
    # with open("animation01.json", "r") as f:
    #     lottie_animation = json.load(f)

    # # ✅ Display the animation inside the placeholder
    # with placeholder:
    #     st_lottie(lottie_animation, speed=1, height=600, key="loading")
    #     time.sleep(1)  # Simulate data loading (Replace with actual logic)

    # # ✅ Remove the animation once loading is complete
    # placeholder.empty()

    st.title("Student Assessment System")

    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "Answer Sheets Verification", 
        "Assignment Cross-Check Verification",
        "OMR Test Analysis"])

    # Answer Verification Tab
    with tab1:
        st.header("Answer Verification")

        # Instructions
        st.markdown("""
        ### Instructions
        1. Upload the "digitized" student answer sheets
            - To digitize answer sheets, use the OCR button below
        2. Upload the answer key
        3. Select the analysis options you want to perform (Peer Comparison, Plagiarism Check, AI Detection)
        4. Click on "Evaluate Answers" to get the analysis report
        """)
        
        # File uploads with expanded file types
        student_answers = st.file_uploader(
            "Upload Student Answers",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="student_answers",
            accept_multiple_files=True,
            help="Upload one or more student answer files"
        )

        # Add OCR button for student answers
        if student_answers and has_unprocessed_images(student_answers):
            if st.button("Convert Images to Text (OCR)", key="ocr_button"):
                with st.spinner("Processing images through OCR..."):
                    progress_text = st.empty()
                    for file in student_answers:
                        if is_image_file(file.name) and file.name not in st.session_state.ocr_results:
                            progress_text.write(f"Processing {file.name}...")
                            text, error = process_ocr(file, lambda msg: progress_text.write(msg))
                            if text:
                                st.session_state.ocr_results[file.name] = text
                                st.success(f"Successfully processed {file.name}")
                            else:
                                st.error(f"Failed to process {file.name}: {error}")
                    progress_text.empty()
                    st.success("OCR processing complete!")

        answer_key = st.file_uploader(
            "Upload Answer Key",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="answer_key",
            help="Upload a single answer key file"
        )

        # Add OCR button for answer key
        if answer_key and is_image_file(answer_key.name) and answer_key.name not in st.session_state.ocr_results:
            if st.button("Convert Answer Key to Text (OCR)", key="ocr_key_button"):
                with st.spinner("Processing answer key through OCR..."):
                    progress_text = st.empty()
                    progress_text.write(f"Processing {answer_key.name}...")
                    text, error = process_ocr(answer_key, lambda msg: progress_text.write(msg))
                    if text:
                        st.session_state.ocr_results[answer_key.name] = text
                        st.success(f"Successfully processed {answer_key.name}")
                    else:
                        st.error(f"Failed to process {answer_key.name}: {error}")
                    progress_text.empty()

        # Check file count and manage checkbox states
        current_file_count = len(student_answers) if student_answers else 0
        
        # Reset all checkboxes if all files are removed
        if current_file_count == 0 and st.session_state.last_files_count > 0:
            reset_checkboxes()
        # Reset peer comparison if files are less than 2
        elif current_file_count < 2 and st.session_state.last_files_count >= 2:
            reset_peer_comparison()
            
        st.session_state.last_files_count = current_file_count

        # Verification options
        col1, col2, col3 = st.columns(3)
        with col1:
            peer_comparison = st.checkbox(
                "Compare Peer-to-Peer",
                disabled=len(student_answers or []) < 2,
                help="Upload at least 2 files to enable peer comparison",
                value=st.session_state.checkboxes['peer_comparison'],
                key='peercheck'
            )
        with col2:
            plagiarism_check = st.checkbox(
                "Plagiarism Check",
                value=st.session_state.checkboxes['plagiarism_check'],
                key='plagiarismcheck'
            )
        with col3:
            ai_detection = st.checkbox(
                "Detect AI-Generated Content",
                value=st.session_state.checkboxes['ai_detection'],
                key='aicheck'
            )

        # Update checkbox states
        st.session_state.checkboxes['peer_comparison'] = peer_comparison
        st.session_state.checkboxes['plagiarism_check'] = plagiarism_check
        st.session_state.checkboxes['ai_detection'] = ai_detection

        if st.button("Evaluate Answers"):
            if not student_answers or not answer_key:
                st.error("Please upload both student answers and answer key files!")
            else:
                # Save answer key temporarily
                temp_key_file = f"temp_key_{answer_key.name}"
                
                # Use OCR result if available, otherwise use original file
                if answer_key.name in st.session_state.ocr_results:
                    with open(temp_key_file, "w", encoding='utf-8') as f:
                        f.write(st.session_state.ocr_results[answer_key.name])
                else:
                    with open(temp_key_file, "wb") as f:
                        f.write(answer_key.getbuffer())

                # Read the answer key content for reuse with error handling
                try:
                    with open(temp_key_file, "r", encoding='utf-8') as f:
                        answer_key_content = f.read().strip()
                except UnicodeDecodeError:
                    with open(temp_key_file, "r", encoding='latin-1') as f:
                        answer_key_content = f.read().strip()

                # Process each student answer
                results_data = []
                for student_answer in student_answers:
                    st.write(f"### Evaluating: {student_answer.name}")
                    
                    # Save student answer temporarily
                    temp_student_file = f"temp_student_{student_answer.name}"
                    
                    # Use OCR result if available, otherwise use original file
                    if student_answer.name in st.session_state.ocr_results:
                        with open(temp_student_file, "w", encoding='utf-8') as f:
                            f.write(st.session_state.ocr_results[student_answer.name])
                    else:
                        with open(temp_student_file, "wb") as f:
                            f.write(student_answer.getbuffer())

                    # Read the student answer content for reuse with error handling
                    try:
                        with open(temp_student_file, "r", encoding='utf-8') as f:
                            student_answer_content = f.read().strip()
                    except UnicodeDecodeError:
                        with open(temp_student_file, "r", encoding='latin-1') as f:
                            student_answer_content = f.read().strip()

                    # Evaluate answers
                    result = evaluate_answers(temp_student_file, temp_key_file)

                    # Clean up student answer file
                    os.remove(temp_student_file)

                    # Display results
                    if result["status"] == "success":
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write("Detailed Analysis:")
                            
                            # Add semantic similarity explanation based on category
                            similarity_explanations = {
                                "very_low": "Very low semantic similarity detected. The answer differs significantly from the expected content.",
                                "low": "Low semantic similarity detected. The answer contains some relevant concepts but misses key points.",
                                "moderate": "Moderate semantic similarity detected. The answer covers several key concepts but may lack depth or precision.",
                                "high": "High semantic similarity detected. The answer covers most key concepts with good understanding.",
                                "very_high": "Very high semantic similarity detected. The answer demonstrates excellent understanding of the concepts."
                            }
                            
                            # Display semantic similarity explanation
                            st.info(similarity_explanations[result["similarity_category"]])
                            
                            # Display detailed metrics
                            for detail in result["details"]:
                                st.write(detail)
                                
                            # Add note about semantic similarity recognition
                            if result["similarity_category"] in ["high", "very_high"]:
                                st.success("✓ Semantically similar content recognized and scored appropriately.")
                        with col2:
                            # Determine color based on score
                            score_color = "normal"
                            if result['overall_score'] < 30:
                                score_color = "inverse"  # For low scores, use inverse (typically red)
                                
                            st.metric(
                                "Score",
                                f"{result['overall_score']:.1f}%",
                                delta=None,
                                delta_color=score_color
                            )
                            
                            # Add category label
                            category_labels = {
                                "very_low": "❌ Very Low",
                                "low": "⚠️ Low",
                                "moderate": "ℹ️ Moderate",
                                "high": "✅ High",
                                "very_high": "🌟 Excellent"
                            }
                            st.markdown(f"**Similarity Category:**  \n{category_labels[result['similarity_category']]}")
                    else:
                        st.error(f"Evaluation failed: {result['message']}")
                    
                    st.markdown("---")

                with st.container():
                    st.markdown("""
                        <style>
                        .report-container {
                            background-color: rgba(89, 37, 193, 0.1);
                            border-radius: 10px;
                            padding: 20px;
                            margin: 10px 0;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="report-container">', unsafe_allow_html=True)
                    
                    # Process files and generate report
                    temp_files = []
                    try:
                        for student_answer in student_answers:
                            temp_file = f"temp_{student_answer.name}"
                            if student_answer.name in st.session_state.ocr_results:
                                with open(temp_file, "w", encoding='utf-8') as f:
                                    f.write(st.session_state.ocr_results[student_answer.name])
                            else:
                                with open(temp_file, "wb") as f:
                                    f.write(student_answer.getbuffer())
                            temp_files.append(temp_file)

                        results_data = []
                    
                        # Generate report sections based on selected options
                        if peer_comparison:
                            results_data.extend(generate_peer_comparison(temp_files))
                        if plagiarism_check:
                            results_data.extend(generate_plagiarism_check(temp_files))
                        if ai_detection:
                            results_data.extend(generate_ai_detection(temp_files))

                        # Generate and offer PDF download
                        if results_data:
                            pdf_bytes = generate_pdf_report(results_data)
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                            )
                            # Clear OCR results after successful report generation
                            clear_ocr_results()
                        else:
                            st.warning("Please select at least one analysis option.")

                    except Exception as e:
                        st.error(f"An error occurred during report generation: {str(e)}")

                    finally:
                        # Clean up temporary files
                        for temp_file in temp_files:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

                # Call appropriate functions based on selected options
                # if peer_comparison:
                #     peer_results = generate_peer_comparison(student_answers)
                #     if peer_results:
                #         for section in peer_results:
                #             st.markdown(f"### {section['title']}")
                #             for content in section['content']:
                #                 st.write(content)

                # if plagiarism_check:
                #     plagiarism_results = generate_plagiarism_check(student_answers)
                #     if plagiarism_results:
                #         for section in plagiarism_results:
                #             st.markdown(f"### {section['title']}")
                #             for content in section['content']:
                #                 st.write(content)

                # if ai_detection:
                #     ai_results = generate_ai_detection(student_answers)
                #     if ai_results:
                #         for section in ai_results:
                #             st.markdown(f"### {section['title']}")
                #             for content in section['content']:
                #                 st.write(content)

                # Clean up answer key file
                os.remove(temp_key_file)

    # Assignment Verification Tab
    with tab2:
        st.header("Assignment Verification")

        # Instructions
        st.markdown("""
        ### Instructions
        1. Upload the "digitized" student assignments
            - To digitize assignments, use the OCR tool provided
        2. Select the analysis options you want to perform (Peer Comparison, Plagiarism Check, AI Detection)
        3. Click on "Generate Report" to get the analysis report
        """)
        
        # File upload for assignments
        uploaded_files = st.file_uploader(
            "Upload Assignment Files",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="assignments",
            help="Supported formats: Text, PDF, Word documents, and Images"
        )

        # Check file count and manage checkbox states
        current_files_count = len(uploaded_files) if uploaded_files else 0
        
        # Reset all checkboxes if all files are removed
        if current_files_count == 0 and st.session_state.last_files_count > 0:
            reset_checkboxes()
        # Reset peer comparison if files are less than 2
        elif current_files_count < 2 and st.session_state.last_files_count >= 2:
            reset_peer_comparison()
            
        st.session_state.last_files_count = current_files_count

        # Verification options
        col1, col2, col3 = st.columns(3)
        with col1:
            peer_comparison = st.checkbox(
                "Compare Peer-to-Peer",
                disabled=len(uploaded_files or []) < 2,
                help="Upload at least 2 files to enable peer comparison",
                value=st.session_state.checkboxes['peer_comparison'],
                key='peer_check'
            )
        with col2:
            plagiarism_check = st.checkbox(
                "Plagiarism Check",
                value=st.session_state.checkboxes['plagiarism_check'],
                key='plagiarism_check'
            )
        with col3:
            ai_detection = st.checkbox(
                "Detect AI-Generated Content",
                value=st.session_state.checkboxes['ai_detection'],
                key='ai_check'
            )

        # Update checkbox states
        st.session_state.checkboxes['peer_comparison'] = peer_comparison
        st.session_state.checkboxes['plagiarism_check'] = plagiarism_check
        st.session_state.checkboxes['ai_detection'] = ai_detection

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            ocr_clicked = st.button("Convert Images to Text (OCR)", use_container_width=True)
        with col2:
            generate_clicked = st.button("Generate Report", use_container_width=True)

        # Display current OCR results
        if st.session_state.ocr_results:
            with st.expander("OCR Results", expanded=True):
                for filename, text in st.session_state.ocr_results.items():
                    st.markdown(f"### 📄 {filename}")
                    st.text_area(
                        "Extracted Text",
                        value=text,
                        height=200,
                        key=f"ocr_display_{filename}"
                    )
                    st.download_button(
                        label=f"Download OCR result",
                        data=text.encode('utf-8'),
                        file_name=f"{os.path.splitext(filename)[0]}_ocr.txt",
                        mime="text/plain;charset=utf-8",
                        key=f"download_display_{filename}"
                    )
                    st.markdown("---")

        # Handle OCR conversion
        if ocr_clicked and uploaded_files:
            image_files = [f for f in uploaded_files if is_image_file(f.name)]
            if not image_files:
                st.warning("No image files found to process. Upload JPG, JPEG, or PNG files.")
            else:
                progress_bar = st.progress(0)
                total_files = len(image_files)
                
                for idx, file in enumerate(image_files):
                    if not is_image_file(file.name):
                        continue
                        
                    text, error = process_ocr(file, lambda msg: st.write(msg))
                    if error:
                        st.error(f"Error processing {file.name}: {error}")
                    else:
                        st.session_state.ocr_results[file.name] = text
                    progress_bar.progress((idx + 1) / total_files)
                
                if st.session_state.ocr_results:
                    st.success("Image processing completed successfully!")

        # Handle report generation
        if generate_clicked:
            if not uploaded_files:
                st.error("Please upload files first!")
            elif has_unprocessed_images(uploaded_files):
                st.error("⚠️ Image files detected! Please use 'Convert Images to Text (OCR)' first.")
                st.info("This ensures all files can be properly analyzed.")
            else:
                with st.container():
                    st.markdown("""
                        <style>
                        .report-container {
                            background-color: rgba(89, 37, 193, 0.1);
                            border-radius: 10px;
                            padding: 20px;
                            margin: 10px 0;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="report-container">', unsafe_allow_html=True)
                    
                    # Process files and generate report
                    temp_files = []
                    try:
                        for uploaded_file in uploaded_files:
                            temp_file = f"temp_{uploaded_file.name}"
                            if uploaded_file.name in st.session_state.ocr_results:
                                with open(temp_file, "w", encoding='utf-8') as f:
                                    f.write(st.session_state.ocr_results[uploaded_file.name])
                            else:
                                with open(temp_file, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                            temp_files.append(temp_file)

                        results_data = []
                    
                        # Generate report sections based on selected options
                        if peer_comparison:
                            results_data.extend(generate_peer_comparison(temp_files))
                        if plagiarism_check:
                            results_data.extend(generate_plagiarism_check(temp_files))
                        if ai_detection:
                            results_data.extend(generate_ai_detection(temp_files))

                        # Generate and offer PDF download
                        if results_data:
                            pdf_bytes = generate_pdf_report(results_data)
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                            )
                            # Clear OCR results after successful report generation
                            clear_ocr_results()
                        else:
                            st.warning("Please select at least one analysis option.")

                    except Exception as e:
                        st.error(f"An error occurred during report generation: {str(e)}")

                    finally:
                        # Clean up temporary files
                        for temp_file in temp_files:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

    # OMR Test Analysis Tab
    with tab3:
        st.header("OMR Test Analysis")
        
        # Instructions
        st.markdown("""
        ### Instructions
        1. Configure the OMR sheet format
        2. Upload a clear image of the correct answer OMR sheet
        3. Upload student OMR answer sheets
        4. Each sheet should have:
           - Clear bubbles marked with dark pen/pencil
           - All 4 corners visible
           - Good lighting and no shadows
        """)
        
        # OMR Configuration
        st.subheader("OMR Configuration")
        col1, col2 = st.columns(2)
        with col1:
            questions_count = st.number_input(
                "Number of Questions",
                min_value=1,
                max_value=100,
                value=20,
                help="Enter the total number of questions in the OMR sheet"
            )
        with col2:
            options_count = st.number_input(
                "Options per Question",
                min_value=2,
                max_value=10,
                value=5,
                help="Enter the number of options per question (e.g., 5 for A,B,C,D,E)"
            )
        
        # Configure button
        if st.button("Configure OMR Format"):
            if st.session_state.omr_processor.configure(questions_count, options_count):
                st.success(f"✅ OMR format configured: {questions_count} questions with {options_count} options each")
            else:
                st.error("Failed to configure OMR format")
        
        st.markdown("---")
        
        # File upload for correct answer OMR sheet
        correct_omr = st.file_uploader(
            "Upload Correct Answer OMR Sheet",
            type=["jpg", "jpeg", "png"],
            key="correct_omr",
            help="Upload the correct answer OMR sheet"
        )
        
        # File upload for student OMR sheets
        student_omr_sheets = st.file_uploader(
            "Upload Student OMR Sheets",
            type=["jpg", "jpeg", "png"],
            key="student_omr",
            accept_multiple_files=True,
            help="Upload one or more student OMR answer sheets"
        )
        
        if st.button("Evaluate OMR Sheets"):
            if not st.session_state.omr_processor.is_configured:
                st.error("Please configure the OMR format first!")
            elif not correct_omr or not student_omr_sheets:
                st.error("Please upload both correct answer sheet and student answer sheets!")
            else:
                # Process answer key first
                if st.session_state.omr_processor.process_answer_key(correct_omr.getvalue()):
                    st.success("✅ Answer key processed successfully!")
                    st.markdown("### 📊 OMR Evaluation Results")
                    
                    # Create a DataFrame to store results
                    results_data = []
                    
                    # Process each student's OMR sheet
                    for student_sheet in student_omr_sheets:
                        st.write(f"### Evaluating: {student_sheet.name}")
                        
                        result = st.session_state.omr_processor.evaluate_answer_sheet(student_sheet.getvalue())
                        
                        if result["status"] == "success":
                            # Display results
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"Total Questions: {result['total_questions']}")
                                st.write(f"Correct Answers: {result['correct_answers']}")
                                
                                # Display answer comparison
                                st.markdown("#### Answer Comparison")
                                
                                # Store question-wise answers for Excel
                                question_answers = []
                                student_answers = result.get('marked_answers', [])
                                correct_answers = result.get('correct_answers_key', [])
                                
                                for q_num in range(result['total_questions']):
                                    student_ans = student_answers[q_num] if q_num < len(student_answers) else -1
                                    correct_ans = correct_answers[q_num] if q_num < len(correct_answers) else -1
                                    
                                    student_choice = chr(65 + student_ans) if student_ans >= 0 else "No answer"
                                    correct_choice = chr(65 + correct_ans) if correct_ans >= 0 else "No answer"
                                    is_correct = student_ans == correct_ans
                                    
                                    st.write(
                                        f"Q{q_num + 1}: Your answer: {student_choice} | "
                                        f"Correct answer: {correct_choice} | "
                                        f"{'✅' if is_correct else '❌'}"
                                    )
                                    
                                    # Add to question answers
                                    question_answers.append({
                                        'Question': f'Q{q_num + 1}',
                                        'Student Answer': student_choice,
                                        'Correct Answer': correct_choice,
                                        'Is Correct': '✓' if is_correct else '✗'
                                    })
                            
                            with col2:
                                st.metric(
                                    "Score",
                                    f"{result['score']:.1f}%"
                                )
                            
                            # Add to results data with detailed answers
                            results_data.append({
                                "Student": os.path.splitext(student_sheet.name)[0],
                                "Score": result['score'],
                                "Correct": result['correct_answers'],
                                "Total": result['total_questions'],
                                "Question_Answers": question_answers
                            })
                        else:
                            st.error(f"Evaluation failed: {result['message']}")
                        
                        st.markdown("---")
                    
                    # Display summary if there are results
                    if results_data:
                        st.markdown("### 📈 Class Summary")
                        scores = [r['Score'] for r in results_data]
                        st.write(f"Class Average: {sum(scores) / len(scores):.1f}%")
                        st.write(f"Highest Score: {max(scores):.1f}%")
                        st.write(f"Lowest Score: {min(scores):.1f}%")
                        
                        # Create Excel export if there are multiple students
                        if len(results_data) > 1:
                            st.markdown("### 📊 Export Results")
                            
                            # Create Excel file
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                # Summary sheet
                                summary_data = []
                                for r in results_data:
                                    summary_data.append({
                                        'Student': r['Student'],
                                        'Score (%)': r['Score'],
                                        'Correct Answers': r['Correct'],
                                        'Total Questions': r['Total']
                                    })
                                
                                summary_df = pd.DataFrame(summary_data)
                                summary_df.loc['Average'] = ['Class Average', 
                                                           summary_df['Score (%)'].mean(),
                                                           summary_df['Correct Answers'].mean(),
                                                           summary_df['Total Questions'].iloc[0]]
                                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                                
                                # Detailed analysis sheet
                                detailed_data = []
                                for result in results_data:
                                    for qa in result['Question_Answers']:
                                        detailed_data.append({
                                            'Student': result['Student'],
                                            'Question': qa['Question'],
                                            'Student Answer': qa['Student Answer'],
                                            'Correct Answer': qa['Correct Answer'],
                                            'Is Correct': qa['Is Correct']
                                        })
                                
                                detailed_df = pd.DataFrame(detailed_data)
                                detailed_df.to_excel(writer, sheet_name='Detailed Analysis', index=False)
                                
                                # Auto-adjust column widths
                                for sheet in writer.book.sheetnames:
                                    ws = writer.book[sheet]
                                    for column in ws.columns:
                                        max_length = 0
                                        column = [cell for cell in column]
                                        for cell in column:
                                            try:
                                                if len(str(cell.value)) > max_length:
                                                    max_length = len(cell.value)
                                            except:
                                                pass
                                        adjusted_width = (max_length + 2)
                                        ws.column_dimensions[column[0].column_letter].width = adjusted_width
                            
                            # Offer Excel download
                            st.download_button(
                                label="📥 Download Detailed Results (Excel)",
                                data=output.getvalue(),
                                file_name=f"omr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error("Failed to process answer key. Please ensure the image is clear and properly aligned.")

    # OCR Tool Tab
    # with tab4:
    #     st.header("Convert Images to Text (OCR)")

    #     # Instructions
    #     st.markdown("""
    #     ### Instructions
    #     1. Upload the image files
    #     2. Click on "Apply OCR" to get the text document
    #     """)
        
    #     # File uploads with expanded file types
    #     img_files = st.file_uploader(
    #         "Upload Image File",
    #         type=["pdf", "docx", "doc", "jpg", "jpeg", "png"],
    #         key="img_file",
    #         help="Upload one or multiple image files",
    #         accept_multiple_files=True 
    #     )
        
    #     if st.button("Apply OCR") and img_files:
    #         if img_files:
    #             # Process the uploaded image file
    #             image_files = [f for f in img_files if is_image_file(f.name)]
    #             if not image_files:
    #                 st.warning("No image files found to process. Upload JPG, JPEG, or PNG files.")
    #             else:
    #                 progress_bar = st.progress(0)
    #                 total_files = len(image_files)
                    
    #                 for idx, file in enumerate(image_files):
    #                     if not is_image_file(file.name):
    #                         continue
                            
    #                     text, error = process_ocr(file, lambda msg: st.write(msg))
    #                     if error:
    #                         st.error(f"Error processing {file.name}: {error}")
    #                     else:
    #                         st.session_state.ocr_results[file.name] = text
    #                     progress_bar.progress((idx + 1) / total_files)
                    
    #                 if st.session_state.ocr_results:
    #                     st.success("Image processing completed successfully!")

    #     # Display current OCR results
    #     if st.session_state.ocr_results:
    #         with st.expander("OCR Results", expanded=True):
    #             for filename, text in st.session_state.ocr_results.items():
    #                 st.markdown(f"### {filename}")
    #                 st.text_area(
    #                     "Extracted Text",
    #                     value=text,
    #                     height=200,
    #                     key=f"ocr_display_{filename}"
    #                 )
    #                 st.download_button(
    #                     label=f"Download OCR result",
    #                     data=text.encode('utf-8'),
    #                     file_name=f"{os.path.splitext(filename)[0]}_ocr.txt",
    #                     mime="text/plain;charset=utf-8",
    #                     key=f"download_display_{filename}"
    #                 )
    #                 st.markdown("---")

if __name__ == "__main__":
    main() 