import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog, messagebox
import os
import mysql.connector
from mysql.connector import Error
from peer_comparison import compare_files  # Import the peer-to-peer comparison function
from plagiarism_check import check_plagiarism  # Import the plagiarism check function
from ai_content import detect_ai_content  # Import the AI content detection function


assignment_file_paths = []  # Global variable to hold the uploaded file paths

# load animation BEGIN
def slowly_load_report():
    """
    Simulates a loading animation in the log area, one block at a time.
    """
    # log_area.insert(tk.END, "\nGenerating new report ")
    loading_blocks = "■ " * 58  # Adjust the number of blocks as needed
    load_animation(loading_blocks, 0)  # Start the animation

def load_animation(loading_blocks, index):
    """
    Adds one block at a time to the loading message.
    """
    if index < len(loading_blocks):
        log_area.insert(tk.END, loading_blocks[index])  # Insert one block
        log_area.see(tk.END)  # Auto-scroll to the end
        root.after(200, load_animation, loading_blocks, index + 1)  # Continue after 200ms
    else:
        # log_area.insert(tk.END, "\nLoading complete!\n")  # Final message
        log_area.see(tk.END)
# load animation END

def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Change as needed
            user='root',       # Replace with your MySQL username
            password='asusi7',  # Replace with your MySQL password
            database=''
        )
        if connection.is_connected():
            return connection
    except Error as e:
        # messagebox.showerror("Error", f"Database connection failed: {e}")
        log_area.insert(tk.END, f"Database connection failed: {e}\n")
        return None


def upload_assignment_file():

    """
    Handles the upload of assignment files and manages the state of the peer-to-peer checkbox.
    """
    global assignment_file_paths
    file_paths = filedialog.askopenfilenames(
        filetypes=[("PDF Files", "*.pdf"), ("DOCX Files", "*.docx"), ("Text Files", "*.txt")]
    )
    new_files = list(file_paths)
    assignment_file_paths.extend(new_files)
    

    # Log uploaded files
    for file_path in new_files:
        log_area.insert(tk.END, f"Uploaded assignment file: {os.path.basename(file_path)}\n")
    
    # Check if more than two PDF files are uploaded
    pdf_count = sum(1 for path in assignment_file_paths if path.endswith(".pdf"))
    if pdf_count > 2:
        peer_checkbox.config(state=tk.DISABLED)
        log_area.insert(tk.END, "Peer-to-peer comparison disabled: More than two files cant't be compared.\n")
    else:
        peer_checkbox.config(state=tk.NORMAL)



def generate_assignment_report():
    """
    Generates an assignment report based on user options.
    """
    if not assignment_file_paths:
        log_area.insert(tk.END, "Error: No assignment files uploaded.\n")
        return
    
    # Clear existing logs to avoid duplicate outputs
    log_area.insert(tk.END, "\nGenerating new report...\n")
    
    try:
        # Perform peer-to-peer comparison if selected
        if checkbox_var.get():
            if len(assignment_file_paths) < 2:
                log_area.insert(tk.END, "\nError: At least two files are required for peer-to-peer comparison.\n")
            else:
                results = compare_files(assignment_file_paths)
                log_area.insert(tk.END, "\n=== Peer-to-Peer Comparison Results ===\n")
                for (file1, file2), similarity in results.items():
                    log_area.insert(tk.END, f"\nComparing files:\n")
                    log_area.insert(tk.END, f"- File 1: {os.path.basename(file1)}\n")
                    log_area.insert(tk.END, f"- File 2: {os.path.basename(file2)}\n")
                    log_area.insert(tk.END, f"- Similarity: {similarity*100:.2f}%\n")
        
        # Perform plagiarism check if selected
        if online_var.get():
            plagiarism_results = check_plagiarism(assignment_file_paths)
            log_area.insert(tk.END, "\n=== Plagiarism Check Results ===\n")
            for file_path, result in plagiarism_results.items():
                log_area.insert(tk.END, f"\n{os.path.basename(file_path)}:\n{result}\n")
        
        # Perform AI content detection if selected
        if ai_var.get():
            ai_results = detect_ai_content(assignment_file_paths)
            log_area.insert(tk.END, "\n=== AI Content Detection Results ===\n")
            for file_path, result in ai_results.items():
                filename = os.path.basename(file_path)
                if result['status'] == 'success':
                    log_area.insert(tk.END, f"\n{filename}:\n")
                    log_area.insert(tk.END, f"- AI Content: {result['ai_percentage']}%\n")
                    log_area.insert(tk.END, f"- Content Length: {result['content_length']} characters\n")
                else:
                    log_area.insert(tk.END, f"\n{filename}: Error - {result['error_message']}\n")
        
    except Exception as e:
        log_area.insert(tk.END, f"Error: An issue occurred during the report generation. Details: {e}\n")


    else:
        # Handle single-file report generation
        report_content = f"Assignment File: {os.path.basename(assignment_file_paths[0])}\n"
        report_content += "Assignment verification results: [Placeholder]\n"
        # log_area.insert(tk.END, report_content)
        # save_report(report_content)

# # Helper function to save report
# def save_report(content):
#     report_path = filedialog.asksaveasfilename(
#         defaultextension=".txt",
#         filetypes=[("Text Files", "*.txt")],
#     )
#     if report_path:
#         with open(report_path, "w") as report_file:
#             report_file.write(content)
#         log_area.insert(tk.END, f"Report saved to: {report_path}\n")
#     else:
#         log_area.insert(tk.END, "Report saving canceled by user.\n")

# Function to clear the log screen
def clear_log_screen():
    """
    Clears the log screen, resets the file paths, and re-enables the peer-to-peer checkbox.
    """
    # Clear the log area
    log_area.delete(1.0, tk.END)
    
    # Reset the file paths list
    global assignment_file_paths
    assignment_file_paths = []  # Reset the uploaded files
    
    # Re-enable the peer-to-peer checkbox
    peer_checkbox.config(state=tk.NORMAL)  # Reset to normal state
    
    # Log reset action
    log_area.insert(tk.END, "App resetted...\n")

def erase_log():
    log_area.delete(1.0, tk.END)
    log_area.insert(tk.END, "Log cleared...\n")



# Create the main window
root = Tk()
root.geometry('638x356')
root.configure(background='#53868B')
root.title('SAS')
#root.resizable(False, False)

# Create a style object
style = ttk.Style()

# Configure the style for the notebook tabs
style.configure("TNotebook.Tab", 
                foreground="black",  # Tab text color
                background="#53868B",  # Tab background color
                padding=[10, 5])  # Padding for the text

# Create a Notebook widget (for tabs)
notebook = ttk.Notebook(root)

# Create two frames (one for each tab)
assignment_tab = Frame(notebook, bg='#53868B')
tab2 = Frame(notebook, bg='#53868B')

# Add the tabs to the notebook
notebook.add(assignment_tab, text='Assignment Verification', padding=5) 
notebook.add(tab2, text='Answer Verification', padding=5)

# Layout for the first tab (Assignment Verification)
top_layout = Frame(assignment_tab, bg='#53868B', pady=10)
top_layout.pack(fill='x', padx=10)

# File upload button
upload_button = Button(top_layout, text="Upload Assignment File", command=upload_assignment_file)
upload_button.pack(side='left', padx=10)

# Frame for checkboxes (placed on the next line)
checkbox_layout = Frame(assignment_tab, bg='#53868B', pady=10)
checkbox_layout.pack(fill='x', padx=10)

# Clear log button
clear_button = Button(top_layout, text="Reset", command=clear_log_screen, bg="#FF5733")
clear_button.pack(side='right', padx=5)
erase_button = Button(top_layout, text="Clear Log", command=erase_log, bg="#FFA500")
erase_button.pack(side='right', padx=5)

# Checkbox below the upload button
checkbox_var = tk.BooleanVar()
online_var = tk.BooleanVar()
ai_var = tk.BooleanVar()

peer_checkbox = Checkbutton(checkbox_layout, text="Compare Peer-to-Peer", variable=checkbox_var, bg='#53868B', fg='black')
peer_checkbox.pack(side='left', padx=10)

online_checkbox = Checkbutton(checkbox_layout, text="Plagiarism Check", variable=online_var, bg='#53868B', fg='black')
online_checkbox.pack(side='left', padx=10)

ai_checkbox = Checkbutton(checkbox_layout, text="Detect AI-Generated Content", variable=ai_var, bg='#53868B', fg='black')
ai_checkbox.pack(side='left', padx=10)

# Generate report button
generate_button = Button(top_layout, text="Generate Report", command=generate_assignment_report, bg="#4CAF50")
generate_button.pack(side='left', padx=10)

# Log area at the bottom
bottom_layout = Frame(assignment_tab, bg='#53868B')
bottom_layout.pack(fill='both', padx=10, pady=10, expand=True)

# Logs Text widget
log_area = Text(bottom_layout, height=8, width=70, wrap=tk.WORD, bg='black', fg='white', bd=3)
log_area.pack(fill='both', expand=True)

# Pack the notebook into the main window
notebook.pack(fill='both', expand=True)

# Start the main loop
root.mainloop()
