import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from datetime import datetime

class RenderCheckFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Variables for Render Check 1
        self.originals_path_1 = tk.StringVar()
        self.transcode_path_1 = tk.StringVar()
        self.enable_logging_1 = tk.BooleanVar(value=False)
        # Variables for Render Check 2
        self.originals_path_2 = tk.StringVar()
        self.transcode_path_2 = tk.StringVar()
        self.enable_logging_2 = tk.BooleanVar(value=False)
        # Logging directory and shared paths
        self.render_check_path = os.path.expanduser("~/Library/RenderCheck")
        self.log_path = os.path.expanduser("~/Desktop/RenderCheckLogs")
        os.makedirs(self.render_check_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)
        self.create_gui()
    
    def create_gui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # --- RENDER CHECK 1 ---
        outer_frame_1 = tk.Frame(main_frame, highlightthickness=1,
                                 highlightbackground="white", highlightcolor="white")
        outer_frame_1.pack(fill="x", pady=(0, 10))
        frame_1 = ttk.LabelFrame(outer_frame_1, text="Render Check 1", style="Header.TLabel")
        frame_1.pack(fill="x", padx=5, pady=5)
        
        # Row 1: Camera Originals for Render Check 1
        row_1 = ttk.Frame(frame_1, padding=5)
        row_1.pack(fill="x")
        ttk.Label(row_1, text="Camera Originals:", style="DIT.TLabel").pack(side="left", padx=5)
        entry_orig_1 = ttk.Entry(row_1, textvariable=self.originals_path_1, width=40)
        entry_orig_1.pack(side="left", padx=5)
        ttk.Button(row_1, text="Browse", style="DIT.TButton",
                   command=lambda: self.browse_folder(self.originals_path_1)).pack(side="left", padx=5)
        
        # Row 2: Transcodes for Render Check 1
        row_2 = ttk.Frame(frame_1, padding=5)
        row_2.pack(fill="x")
        ttk.Label(row_2, text="Transcodes:", style="DIT.TLabel").pack(side="left", padx=17)
        entry_trans_1 = ttk.Entry(row_2, textvariable=self.transcode_path_1, width=40)
        entry_trans_1.pack(side="left", padx=5)
        ttk.Button(row_2, text="Browse", style="DIT.TButton",
                   command=lambda: self.browse_folder(self.transcode_path_1,
                                                       os.path.dirname(self.originals_path_1.get()) if self.originals_path_1.get() else None)
                  ).pack(side="left", padx=5)
        
        # Row 3: Enable Logging and Check Renders Button for Render Check 1
        row_3 = ttk.Frame(frame_1, padding=5)
        row_3.pack(fill="x")
        ttk.Checkbutton(row_3, text="Enable Logging", variable=self.enable_logging_1, style="DIT.TCheckbutton").pack(side="left", padx=5)
        ttk.Button(row_3, text="Check Renders", style="DIT.TButton",
                   command=self.run_comparison_1).pack(side="right", padx=5)
        
        # --- RENDER CHECK 2 ---
        outer_frame_2 = tk.Frame(main_frame, highlightthickness=1,
                                 highlightbackground="white", highlightcolor="white")
        outer_frame_2.pack(fill="x", pady=(0, 10))
        frame_2 = ttk.LabelFrame(outer_frame_2, text="Render Check 2", style="Header.TLabel")
        frame_2.pack(fill="x", padx=5, pady=5)
        
        # Row 1: Camera Originals for Render Check 2
        row_1_2 = ttk.Frame(frame_2, padding=5)
        row_1_2.pack(fill="x")
        ttk.Label(row_1_2, text="Camera Originals:", style="DIT.TLabel").pack(side="left", padx=5)
        entry_orig_2 = ttk.Entry(row_1_2, textvariable=self.originals_path_2, width=40)
        entry_orig_2.pack(side="left", padx=5)
        ttk.Button(row_1_2, text="Browse", style="DIT.TButton",
                   command=lambda: self.browse_folder(self.originals_path_2)).pack(side="left", padx=5)
        
        # Row 2: Transcodes for Render Check 2
        row_2_2 = ttk.Frame(frame_2, padding=5)
        row_2_2.pack(fill="x")
        ttk.Label(row_2_2, text="Transcodes:", style="DIT.TLabel").pack(side="left", padx=17)
        entry_trans_2 = ttk.Entry(row_2_2, textvariable=self.transcode_path_2, width=40)
        entry_trans_2.pack(side="left", padx=5)
        ttk.Button(row_2_2, text="Browse", style="DIT.TButton",
                   command=lambda: self.browse_folder(self.transcode_path_2,
                                                       os.path.dirname(self.originals_path_2.get()) if self.originals_path_2.get() else None)
                  ).pack(side="left", padx=5)
        
        # Row 3: Enable Logging and Check Renders Button for Render Check 2
        row_3_2 = ttk.Frame(frame_2, padding=5)
        row_3_2.pack(fill="x")
        ttk.Checkbutton(row_3_2, text="Enable Logging", variable=self.enable_logging_2, style="DIT.TCheckbutton").pack(side="left", padx=5)
        ttk.Button(row_3_2, text="Check Renders", style="DIT.TButton",
                   command=self.run_comparison_2).pack(side="right", padx=5)
        
        # --- LOG DIRECTORY BUTTON & STATUS WINDOW ---
        row_log = ttk.Frame(main_frame, padding=5)
        row_log.pack(fill="x")
        ttk.Button(row_log, text="Log Directory", style="DIT.TButton",
                   command=self.choose_log_directory).pack(side="left", padx=5)
        self.log_path_label = ttk.Label(row_log, text=f"Logs will be saved to: {self.log_path}", style="DIT.TLabel")
        self.log_path_label.pack(side="left", padx=10)
        
        # Status Window with Scrollbar
        status_frame = ttk.Frame(main_frame, padding=5)
        status_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(status_frame)
        scrollbar.pack(side="right", fill="y")
        self.results_text = tk.Text(status_frame, height=10, width=80, bg="black", fg="white")
        self.results_text.pack(side="left", fill="both", expand=True)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)
        
        # --- CLEAR STATUS BUTTON ---
        clear_frame = ttk.Frame(main_frame, padding=5)
        clear_frame.pack(fill="x")
        ttk.Button(clear_frame, text="Clear Status", style="DIT.TButton", command=self.clear_status).pack(side="left", padx=5)
        
        # Add initialization message to status window
        self.results_text.insert(tk.END, "Render Check Tool Started.\n")
        self.results_text.insert(tk.END, "Select your source of Camera Originals, then select your source of Transcodes and click 'Check Render' to verify all your Dailies have been generated.\n")
    
    def browse_folder(self, path_var, initial_dir=None):
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        if folder_path:
            path_var.set(folder_path)
    
    def choose_log_directory(self):
        directory = filedialog.askdirectory(title="Select Log Directory")
        if directory:
            self.log_path = directory
            self.log_path_label.config(text=f"Logs will be saved to: {self.log_path}")
            messagebox.showinfo("Log Directory", f"Log directory set to: {directory}")
    
    def clear_status(self):
        self.results_text.delete("1.0", tk.END)
    
    def write_to_log(self, message, enable_logging_flag):
        if enable_logging_flag:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.log_path, f"RenderCheck_Log_{timestamp}.txt")
            with open(log_file, 'a') as f:
                f.write(f"{message}\n")
    
    def process_camera_originals(self, folder_path):
        file_list = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in ('.mov', '.mxf', '.rdc', '.cine', '.mp4', '.ari', '.arx', '.dng')):
                    file_list.append(os.path.join(root, file))
        processed_names = set()
        for file_path in file_list:
            filename = os.path.basename(file_path)
            name = re.sub(r'\.(MXF|mxf|mov|MOV|RDC|cine|mp4|MP4|ari|arx|dng|DNG)$', '', filename)
            if any(x in name for x in ('Cine', 'Blackmagic', '_201')):
                processed_name = name
            else:
                processed_name = name[:10]
            processed_name = re.sub(r'_[0-9A-Z]$', '', processed_name)
            processed_name = re.sub(r'_$', '', processed_name)
            processed_names.add(processed_name)
        return processed_names
    
    def process_transcodes(self, folder_path):
        file_list = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mov', '.mxf')):
                    if not re.search(r'_A\d+\.mxf$', file):
                        file_list.append(os.path.join(root, file))
        processed_names = set()
        for file_path in file_list:
            filename = os.path.basename(file_path)
            name = re.sub(r'\.(mxf|mov)$', '', filename)
            if any(x in name for x in ('Cine', 'Blackmagic', '_201')):
                processed_name = name
            else:
                processed_name = name[:10]
            processed_name = re.sub(r'_[0-9A-Z]$', '', processed_name)
            processed_name = re.sub(r'_$', '', processed_name)
            processed_names.add(processed_name)
        return processed_names
    
    def run_comparison_1(self):
        self.results_text.insert(tk.END, "\n===== Render Check 1 =====\n")
        self._run_comparison(self.originals_path_1.get(), self.transcode_path_1.get(), self.enable_logging_1.get())
    
    def run_comparison_2(self):
        self.results_text.insert(tk.END, "\n===== Render Check 2 =====\n")
        self._run_comparison(self.originals_path_2.get(), self.transcode_path_2.get(), self.enable_logging_2.get())
    
    def _run_comparison(self, originals_path, transcodes_path, enable_logging_flag):
        if not originals_path:
            msg = "Please select Camera Originals directory.\n"
            self.results_text.insert(tk.END, msg)
            return
        if not transcodes_path:
            msg = "Please select Transcodes directory.\n"
            self.results_text.insert(tk.END, msg)
            return
        
        originals = self.process_camera_originals(originals_path)
        transcodes = self.process_transcodes(transcodes_path)
        
        msg_info = (
            f"Camera Originals Directory: {originals_path}\n"
            f"Transcodes Directory: {transcodes_path}\n"
            f"Found {len(originals)} original files\n"
        )
        self.results_text.insert(tk.END, msg_info)
        self.write_to_log(msg_info, enable_logging_flag)
        
        missing_in_transcodes = originals - transcodes
        extra_in_transcodes = transcodes - originals
        
        if not missing_in_transcodes and not extra_in_transcodes:
            result = "Success! All files match.\n"
        else:
            result = ""
            if missing_in_transcodes:
                result += "\nMissing in transcodes:\n" + "\n".join(sorted(missing_in_transcodes)) + "\n"
            if extra_in_transcodes:
                result += "\nExtra files in transcodes:\n" + "\n".join(sorted(extra_in_transcodes)) + "\n"
        
        self.results_text.insert(tk.END, result)
        self.write_to_log(result, enable_logging_flag)
        self.results_text.see("1.0")