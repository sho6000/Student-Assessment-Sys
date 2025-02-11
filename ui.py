import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinter import font, Text, Button, Frame, Tk, Checkbutton, BooleanVar
import os
# import mysql.connector
# from mysql.connector import Error
from peer_comparison import compare_files
from plagiarism_check import check_plagiarism
from ai_content import detect_ai_content
from ocr import perform_ocr, save_ocr_result
# from sentence_transformers import SentenceTransformer, util
# import re
from ans_eval import evaluate_answers

class StudentAssessmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Assessment System")
        
        # Increase window size for better layout
        self.root.geometry("800x600")
        self.root.config(bg="#f4f4f9")
        
        # Store uploaded file paths
        self.assignment_file_paths = []
        self.submission_file = ""
        self.answer_key_file = ""
        self.format_key_file = ""
        
        self.label_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=10, weight="normal")
        self.text_font = font.Font(family="Courier New", size=10)
        
        self.create_widgets()

    def create_widgets(self):
        # Main title
        self.title_label = tk.Label(
            self.root, 
            text="Student Assessment System",
            font=("Helvetica", 24, "bold"),
            bg="#f4f4f9",
            fg="#2c3e50"
        )
        self.title_label.pack(pady=20)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=10)

        # Create tabs
        self.answer_tab = ttk.Frame(self.notebook)
        self.assignment_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.answer_tab, text='Answer Verification')
        self.notebook.add(self.assignment_tab, text='Assignment Verification')

        # Setup both tabs
        self.setup_answer_tab()
        self.setup_assignment_tab()

    def setup_assignment_tab(self):
        # Upload frame
        upload_frame = ttk.LabelFrame(self.assignment_tab, text="Upload Files", padding=20)
        upload_frame.pack(fill='x', padx=20, pady=10)

        # File upload button
        ttk.Button(
            upload_frame,
            text="Upload Assignment Files",
            command=self.upload_assignment_file,
            style='Accent.TButton'
        ).pack(side='left', padx=5)

        # OCR button
        ttk.Button(
            upload_frame,
            text="Convert to Text (OCR)",
            command=self.perform_ocr_conversion,
            style='Accent.TButton'
        ).pack(side='left', padx=5)

        # Clear buttons
        ttk.Button(
            upload_frame,
            text="Reset",
            command=self.clear_log_screen,
            style='Accent.TButton'
        ).pack(side='right', padx=5)
        
        ttk.Button(
            upload_frame,
            text="Clear Log",
            command=self.erase_log,
            style='Accent.TButton'
        ).pack(side='right', padx=5)

        # Checkbox frame
        checkbox_frame = ttk.LabelFrame(self.assignment_tab, text="Verification Options", padding=10)
        checkbox_frame.pack(fill='x', padx=20, pady=10)

        # Checkboxes
        self.checkbox_var = BooleanVar()
        self.online_var = BooleanVar()
        self.ai_var = BooleanVar()

        ttk.Checkbutton(
            checkbox_frame,
            text="Compare Peer-to-Peer",
            variable=self.checkbox_var
        ).pack(side='left', padx=10)

        ttk.Checkbutton(
            checkbox_frame,
            text="Plagiarism Check",
            variable=self.online_var
        ).pack(side='left', padx=10)

        ttk.Checkbutton(
            checkbox_frame,
            text="Detect AI-Generated Content",
            variable=self.ai_var
        ).pack(side='left', padx=10)

        # Generate report button
        ttk.Button(
            self.assignment_tab,
            text="Generate Report",
            command=self.generate_assignment_report,
            style='Accent.TButton'
        ).pack(pady=10)

        # Log area
        log_frame = ttk.LabelFrame(self.assignment_tab, text="Processing Log", padding=20)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.log_area = Text(
            log_frame,
            height=10,
            width=50,
            font=self.text_font,
            wrap="word",
            bg='white',
            fg='black'
        )
        self.log_area.pack(fill='both', expand=True)

    def setup_answer_tab(self):
        # Frame for file uploads
        upload_frame = ttk.LabelFrame(self.answer_tab, text="Upload Files", padding=20)
        upload_frame.pack(fill='x', padx=20, pady=10)

        # Submission upload section
        submission_frame = ttk.Frame(upload_frame)
        submission_frame.pack(fill='x', pady=5)
        
        ttk.Label(submission_frame, text="Student Answer:", font=self.label_font).pack(side='left')
        self.submission_label = ttk.Label(submission_frame, text="No file selected", font=self.text_font)
        self.submission_label.pack(side='left', padx=10)
        ttk.Button(
            submission_frame,
            text="Choose File",
            command=self.upload_submission,
            style='Accent.TButton'
        ).pack(side='right')

        # Answer key upload section
        key_frame = ttk.Frame(upload_frame)
        key_frame.pack(fill='x', pady=5)
        
        ttk.Label(key_frame, text="Answer Key:", font=self.label_font).pack(side='left')
        self.answer_key_label = ttk.Label(key_frame, text="No file selected", font=self.text_font)
        self.answer_key_label.pack(side='left', padx=10)
        ttk.Button(
            key_frame,
            text="Choose File",
            command=self.upload_answer_key,
            style='Accent.TButton'
        ).pack(side='right')

        # Evaluate button
        ttk.Button(
            self.answer_tab,
            text="Evaluate Answer",
            command=self.evaluate_submission,
            style='Accent.TButton'
        ).pack(pady=20)

        # Report section
        report_frame = ttk.LabelFrame(self.answer_tab, text="Evaluation Report", padding=20)
        report_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.report_text = Text(
            report_frame,
            height=10,
            width=50,
            font=self.text_font,
            wrap="word",
            bg='white',
            fg='black'
        )
        self.report_text.pack(fill='both', expand=True)

    # Methods from the original UI
    def upload_assignment_file(self):
        file_paths = filedialog.askopenfilenames(title="Select Assignment Files", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])

        for file_path in file_paths:
            if file_path not in self.assignment_file_paths:
                self.assignment_file_paths.append(file_path)
                self.log_area.insert(tk.END, f"Uploaded: {os.path.basename(file_path)}\n")
            else:
                self.log_area.insert(tk.END, f"File already uploaded: {os.path.basename(file_path)}\n")

        if not self.assignment_file_paths:
            self.log_area.insert(tk.END, "No files were selected.\n")

    def upload_submission(self):
        file_path = filedialog.askopenfilename(
            filetypes=(("Text Files", "*.txt"), ("PDF Files", "*.pdf"), ("All Files", "*.*"))
        )
        if file_path:
            self.submission_file = file_path  # Store the full path
            self.submission_label.config(text=os.path.basename(file_path))
            messagebox.showinfo("Success", "Answer file uploaded successfully!")

    def upload_answer_key(self):
        file_path = filedialog.askopenfilename(
            filetypes=(("Text Files", "*.txt"), ("PDF Files", "*.pdf"), ("All Files", "*.*"))
        )
        if file_path:
            self.answer_key_file = file_path  # Store the full path
            self.answer_key_label.config(text=os.path.basename(file_path))
            messagebox.showinfo("Success", "Answer key uploaded successfully!")

    # Existing methods from previous implementation
    def generate_assignment_report(self):
        if not self.assignment_file_paths:
            self.log_area.insert(tk.END, "Error: No assignment files uploaded.\n")
            return
    
        self.log_area.insert(tk.END, "\nGenerating new report...\n")
    
        try:
            # Peer-to-peer comparison
            if self.checkbox_var.get():
                if len(self.assignment_file_paths) < 2:
                    self.log_area.insert(tk.END, "\nError: At least two files are required for peer-to-peer comparison.\n")
                else:
                    results = compare_files(self.assignment_file_paths)
                    self.log_area.insert(tk.END, "\n=== Peer-to-Peer Comparison Results ===\n")
                
                    for files, similarity in results.items():
                        if len(files) == 2:
                            file1, file2 = files
                            self.log_area.insert(tk.END, f"Comparing:\n - File 1: {os.path.basename(file1)}\n")
                            self.log_area.insert(tk.END, f" - File 2: {os.path.basename(file2)}\n")
                            self.log_area.insert(tk.END, f" - Similarity: {similarity * 100:.2f}%\n")
                        else:
                            self.log_area.insert(tk.END, "Unexpected result structure in peer comparison.\n")
        
            # Plagiarism check
            if self.online_var.get():
                plagiarism_results = check_plagiarism(self.assignment_file_paths)
                self.log_area.insert(tk.END, "\n=== Plagiarism Check Results ===\n")
                for file_path, result in plagiarism_results.items():
                    self.log_area.insert(tk.END, f"\n{os.path.basename(file_path)}:\n{result}\n")
        
            # AI content detection
            if self.ai_var.get():
                ai_results = detect_ai_content(self.assignment_file_paths)
                self.log_area.insert(tk.END, "\n=== AI Content Detection Results ===\n")
                for file_path, result in ai_results.items():
                    filename = os.path.basename(file_path)
                    if result['status'] == 'success':
                        self.log_area.insert(tk.END, f"\n{filename}:\n")
                        self.log_area.insert(tk.END, f"- AI Content: {result['ai_percentage']}%\n")
                        self.log_area.insert(tk.END, f"- Content Length: {result['content_length']} characters\n")
                    else:
                        self.log_area.insert(tk.END, f"\n{filename}: Error - {result['error_message']}\n")
    
        except Exception as e:
            self.log_area.insert(tk.END, f"Error: An issue occurred during the report generation. Details: {e}\n")


    def evaluate_submission(self):
        # Check if files are uploaded
        if not self.submission_file or not self.answer_key_file:
            messagebox.showerror("Error", "Both the student answer and the answer key must be uploaded!")
            return

        # Call the evaluation function with the stored file paths
        result = evaluate_answers(self.submission_file, self.answer_key_file)

        # Display the results
        if result["status"] == "success":
            report = "Evaluation Report:\n" + "="*20 + "\n\n"
            report += f"Overall Score: {result['overall_score']:.2f}%\n\n"
            report += "Detailed Analysis:\n" + "-"*20 + "\n"
            report += "\n".join(result["details"])
            
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)
            messagebox.showinfo("Success", "Evaluation completed successfully!")
        else:
            messagebox.showerror("Error", f"Evaluation failed: {result['message']}")


    def clear_log_screen(self):
        self.log_area.delete(1.0, tk.END)
        self.assignment_file_paths = []
        self.checkbox_var.set(False)
        self.log_area.insert(tk.END, "App resetted...\n")

    def erase_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "Log cleared...\n")

    def perform_ocr_conversion(self):
        if not self.assignment_file_paths:
            self.log_area.insert(tk.END, "Error: No files uploaded for OCR conversion.\n")
            return
        
        self.log_area.insert(tk.END, "\nStarting OCR conversion...\n")
        
        for file_path in self.assignment_file_paths:
            filename = os.path.basename(file_path)
            self.log_area.insert(tk.END, f"\nProcessing: {filename}\n")
            
            text, error = perform_ocr(file_path, lambda msg: self.log_area.insert(tk.END, msg))
            
            if error:
                self.log_area.insert(tk.END, f"Error processing {filename}: {error}\n")
                continue
            
            output_path = os.path.splitext(file_path)[0] + "_ocr.txt"
            if save_ocr_result(text, output_path):
                self.log_area.insert(tk.END, f"OCR result saved to: {os.path.basename(output_path)}\n")
            else:
                self.log_area.insert(tk.END, f"Error saving OCR result for {filename}\n")
        
        self.log_area.insert(tk.END, "\nOCR conversion completed!\n")

# Configure style
def configure_styles():
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Helvetica', 10))
    return style

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    style = configure_styles()
    app = StudentAssessmentApp(root)
    root.mainloop()