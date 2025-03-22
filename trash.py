import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil

def move_drx_files(target_directory, output_callback=None):
    trash_dir = os.path.expanduser("~/.Trash")
    if not os.path.isdir(trash_dir):
        if output_callback:
            output_callback(f"Error: Trash directory not found: {trash_dir}")
        return
    if not os.access(trash_dir, os.W_OK):
        if output_callback:
            output_callback(f"Error: No write permission for Trash directory: {trash_dir}")
        return
    files_moved = 0
    files_failed = 0
    try:
        for root_dir, dirs, files in os.walk(target_directory):
            for file in files:
                if file.lower().endswith(".drx"):
                    src = os.path.join(root_dir, file)
                    dest = os.path.join(trash_dir, file)
                    base, ext = os.path.splitext(file)
                    counter = 1
                    if not os.access(src, os.R_OK):
                        if output_callback:
                            output_callback(f"Error: No read permission for file: {src}")
                        files_failed += 1
                        continue
                    while os.path.exists(dest):
                        dest = os.path.join(trash_dir, f"{base}_{counter}{ext}")
                        counter += 1
                    try:
                        if output_callback:
                            output_callback(f"Moving: {src} -> {dest}")
                        shutil.move(src, dest)
                        files_moved += 1
                    except (PermissionError, OSError) as e:
                        if output_callback:
                            output_callback(f"Error moving file {src}: {str(e)}")
                        files_failed += 1
    except Exception as e:
        if output_callback:
            output_callback(f"An unexpected error occurred: {str(e)}")
    if output_callback:
        output_callback(f"Total .drx files moved: {files_moved}")
        if files_failed > 0:
            output_callback(f"Failed to move {files_failed} files due to permission errors.")

class TrashDrxFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_directory = ""
        self.create_widgets()
        self.report_app_started()
    
    def create_widgets(self):
        self.load_btn = ttk.Button(self, text="Load Directory", style="DIT.TButton", command=self.load_directory)
        self.load_btn.pack(pady=10)
        self.dir_label = ttk.Label(self, text="No directory selected", style="DIT.TLabel")
        self.dir_label.pack(pady=5)
        self.trash_btn = ttk.Button(self, text="Trash .drx", style="DIT.TButton", command=self.trash_drx)
        self.trash_btn.pack(pady=10)
        self.output_text = tk.Text(self, height=15, width=100)
        self.output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        self.clear_btn = ttk.Button(self.bottom_frame, text="Clear Status", style="DIT.TButton", command=self.clear_status)
        self.clear_btn.pack(side=tk.LEFT)
    
    def load_directory(self):
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            self.selected_directory = directory
            self.dir_label.config(text=f"Selected Directory: {directory}")
            self.log_output(f"Loaded directory: {directory}")
    
    def trash_drx(self):
        if not self.selected_directory:
            messagebox.showerror("Error", "No directory selected. Please load a directory first.")
            return
        if not os.path.exists(self.selected_directory):
            messagebox.showerror("Error", "The selected directory no longer exists.")
            return
        if not os.access(self.selected_directory, os.R_OK):
            messagebox.showerror("Error", "No permission to read the selected directory.")
            return
        self.log_output("Starting to trash .drx files...\n")
        move_drx_files(self.selected_directory, output_callback=self.log_output)
        self.log_output("\nOperation completed.")
    
    def log_output(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
    
    def clear_status(self):
        self.output_text.delete("1.0", tk.END)
    
    def report_app_started(self):
        self.log_output("Trash .drx Tool Started.")
        self.log_output("Ready to remove those pesky .drx files.")