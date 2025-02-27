import streamlit as st
import os
from modules.peer_comparison import compare_files
from modules.plagiarism_check import check_plagiarism
from modules.ai_content import detect_ai_content
from modules.ocr import perform_ocr, save_ocr_result
from modules.ans_eval import evaluate_answers
from fpdf import FPDF
import io
from datetime import datetime

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
            pdf.multi_cell(0, 10, result)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin1')

def main():
    st.set_page_config(
        page_title="Student Assessment System",
        page_icon="assets/pen.jpg",
        layout="wide"
    )
    st.title("Student Assessment System")

    # Create tabs
    tab1, tab2 = st.tabs([
        "Answer Sheets Verification", 
        "Assignment Cross-Check Verification"
    ])

    # Answer Verification Tab
    with tab1:
        st.header("Answer Verification")
        
        # File uploads with expanded file types
        student_answers = st.file_uploader(
            "Upload Student Answers",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="student_answers",
            accept_multiple_files=True,
            help="Upload one or more student answer files"
        )
        answer_key = st.file_uploader(
            "Upload Answer Key",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            key="answer_key",
            help="Upload a single answer key file"
        )

        if st.button("Evaluate Answers"):
            if not student_answers or not answer_key:
                st.error("Please upload both student answers and answer key files!")
            else:
                # Save answer key temporarily
                temp_key_file = f"temp_key_{answer_key.name}"
                with open(temp_key_file, "wb") as f:
                    f.write(answer_key.getbuffer())

                # Process each student answer
                for student_answer in student_answers:
                    st.write(f"### Evaluating: {student_answer.name}")
                    
                    # Save student answer temporarily
                    temp_student_file = f"temp_student_{student_answer.name}"
                    with open(temp_student_file, "wb") as f:
                        f.write(student_answer.getbuffer())

                    # Evaluate answers
                    result = evaluate_answers(temp_student_file, temp_key_file)

                    # Clean up student answer file
                    os.remove(temp_student_file)

                    # Display results
                    if result["status"] == "success":
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write("Detailed Analysis:")
                            for detail in result["details"]:
                                st.write(detail)
                        with col2:
                            st.metric(
                                "Score",
                                f"{result['overall_score']:.1f}%"
                            )
                    else:
                        st.error(f"Evaluation failed: {result['message']}")
                    
                    st.markdown("---")

                # Clean up answer key file
                os.remove(temp_key_file)

    # Assignment Verification Tab
    with tab2:
        st.header("Assignment Verification")
        
        # File upload for assignments with expanded file types
        uploaded_files = st.file_uploader(
            "Upload Assignment Files",
            type=["txt", "pdf", "docx", "doc", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="assignments",
            help="Supported formats: Text, PDF, Word documents, and Images"
        )

        # Verification options
        col1, col2, col3 = st.columns(3)
        with col1:
            peer_comparison = st.checkbox(
                "Compare Peer-to-Peer",
                disabled=len(uploaded_files or []) < 2,
                help="Upload at least 2 files to enable peer comparison"
            )
        with col2:
            plagiarism_check = st.checkbox("Plagiarism Check")
        with col3:
            ai_detection = st.checkbox("Detect AI-Generated Content")

        # Action buttons in one line
        col1, col2 = st.columns(2)
        
        with col1:
            ocr_clicked = st.button("Convert to Text (OCR)", use_container_width=True)
        with col2:
            generate_clicked = st.button("Generate Report", use_container_width=True)

        # Handle OCR conversion
        if ocr_clicked:
            if not uploaded_files:
                st.error("Please upload files first!")
            else:
                for uploaded_file in uploaded_files:
                    temp_file = f"temp_{uploaded_file.name}"
                    with open(temp_file, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    text, error = perform_ocr(temp_file, lambda msg: st.write(msg))
                    
                    if error:
                        st.error(f"Error processing {uploaded_file.name}: {error}")
                    else:
                        output_path = os.path.splitext(temp_file)[0] + "_ocr.txt"
                        if save_ocr_result(text, output_path):
                            st.success(f"OCR result saved to: {os.path.basename(output_path)}")
                            # Provide download button for OCR result
                            with open(output_path, "r") as f:
                                st.download_button(
                                    label=f"Download OCR result for {uploaded_file.name}",
                                    data=f.read(),
                                    file_name=os.path.basename(output_path),
                                    mime="text/plain"
                                )
                        else:
                            st.error(f"Error saving OCR result for {uploaded_file.name}")

                    os.remove(temp_file)
                    if os.path.exists(output_path):
                        os.remove(output_path)

        # Handle report generation
        if generate_clicked:
            if not uploaded_files:
                st.error("Please upload files first!")
            else:
                # Create a container for all results
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
                    
                    # Save uploaded files temporarily
                    temp_files = []
                    for uploaded_file in uploaded_files:
                        temp_file = f"temp_{uploaded_file.name}"
                        with open(temp_file, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        temp_files.append(temp_file)

                    # Initialize results data for PDF
                    results_data = []
                    
                    try:
                        # Peer-to-peer comparison
                        if peer_comparison:
                            peer_results = []
                            st.markdown("### 🔄 Peer-to-Peer Comparison Results")
                            with st.spinner('Comparing files...'):
                                results = compare_files(temp_files)
                                for files, similarity in results.items():
                                    if len(files) == 2:
                                        file1, file2 = files
                                        st.markdown("---")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write("📄 File 1:", os.path.basename(file1))
                                            st.write("📄 File 2:", os.path.basename(file2))
                                        with col2:
                                            similarity_percentage = similarity * 100
                                            st.metric(
                                                "Similarity Score",
                                                f"{similarity_percentage:.1f}%",
                                                delta=None
                                            )
                                        # Add to PDF results
                                        peer_results.append(
                                            f"Comparing {os.path.basename(file1)} with {os.path.basename(file2)}\n"
                                            f"Similarity Score: {similarity_percentage:.1f}%\n"
                                        )
                            results_data.append({
                                'title': 'Peer-to-Peer Comparison Results',
                                'content': peer_results
                            })

                        # Plagiarism check
                        if plagiarism_check:
                            plagiarism_results_list = []
                            st.markdown("### 🔍 Plagiarism Check Results")
                            plagiarism_results = check_plagiarism(temp_files)
                            for file_path, result in plagiarism_results.items():
                                st.markdown(f"**File: {os.path.basename(file_path)}**")
                                st.info(result)
                                # Add to PDF results
                                plagiarism_results_list.append(
                                    f"File: {os.path.basename(file_path)}\n{result}\n"
                                )
                            results_data.append({
                                'title': 'Plagiarism Check Results',
                                'content': plagiarism_results_list
                            })

                        # AI content detection
                        if ai_detection:
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
                                    # Add to PDF results
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
                            results_data.append({
                                'title': 'AI Content Detection Results',
                                'content': ai_results_list
                            })

                        # Generate PDF report
                        if results_data:
                            pdf_bytes = generate_pdf_report(results_data)
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                            )

                    except Exception as e:
                        st.error(f"An error occurred during report generation: {str(e)}")

                    finally:
                        # Clean up temporary files
                        for temp_file in temp_files:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 