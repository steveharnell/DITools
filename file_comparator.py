import os
import re
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

def scan_drive_attributes(root_path, compare_size, compare_date, compare_creation, skip_hidden=False, skip_mhl=False):
    files_dict = {}
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Exclude specific directories
        dirnames[:] = [d for d in dirnames if d != '_gsdata_']
        if skip_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        rel_dir = os.path.relpath(dirpath, root_path)
        if rel_dir != ".":
            key = rel_dir + os.sep
            files_dict[key] = {"type": "directory"}
        for filename in filenames:
            if filename == ".DS_Store":
                continue
            if skip_mhl and filename.lower().endswith(".mhl"):
                continue
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_path)
            attr = {"type": "file"}
            if compare_size:
                try:
                    attr['size'] = os.path.getsize(full_path)
                except Exception:
                    attr['size'] = None
            if compare_date:
                try:
                    attr['mod_date'] = os.path.getmtime(full_path)
                except Exception:
                    attr['mod_date'] = None
            if compare_creation:
                try:
                    attr['creation_date'] = os.path.getctime(full_path)
                except Exception:
                    attr['creation_date'] = None
            files_dict[rel_path] = attr
    return files_dict

class FileComparatorFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.drive_paths = []
        self.reference_drive = None
        self.log_directory = None
        self.create_widgets()
    
    def create_widgets(self):
        # Top frame with drive management buttons
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5)
        # "Add All Drives" button remains unchanged.
        self.add_button = ttk.Button(top_frame, text="Add All Drives", style="DIT.TButton", command=self.add_all_drives)
        self.add_button.grid(row=0, column=0, padx=5)
        self.clear_button = ttk.Button(top_frame, text="Clear Drives", style="DIT.TButton", command=self.clear_drives)
        self.clear_button.grid(row=0, column=1, padx=5)
        self.set_ref_button = ttk.Button(top_frame, text="Set as Reference", style="DIT.TButton", command=self.set_reference)
        self.set_ref_button.grid(row=0, column=2, padx=5)
        self.auto_ref_button = ttk.Button(top_frame, text="Auto Reference", style="DIT.TButton", command=self.auto_reference)
        self.auto_ref_button.grid(row=0, column=3, padx=5)
        
        # Listbox to show drives and a label for the reference drive
        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, width=80)
        self.listbox.pack(pady=5)
        self.ref_label = ttk.Label(self, text="Reference Drive: Not Set", style="DIT.TLabel")
        self.ref_label.pack(pady=5)
        
        # New small buttons for adding and removing drives, now centered.
        drive_buttons_frame = ttk.Frame(self)
        drive_buttons_frame.pack(pady=2, anchor="center", padx=10)
        # Updated "+" button now calls add_drive for individual drive selection.
        self.plus_button = ttk.Button(drive_buttons_frame, text="+", width=3, command=self.add_drive)
        self.plus_button.pack(side=tk.LEFT, padx=(0,5))
        self.minus_button = ttk.Button(drive_buttons_frame, text="-", width=3, command=self.remove_drive)
        self.minus_button.pack(side=tk.LEFT)
        
        # Options for comparison
        options_frame = ttk.LabelFrame(self, text="Comparison Options", padding=10)
        options_frame.pack(pady=5, fill="x", padx=10)
        self.compare_size_var = tk.BooleanVar(value=True)
        self.compare_date_var = tk.BooleanVar(value=False)
        self.compare_creation_var = tk.BooleanVar(value=False)
        self.skip_hidden_var = tk.BooleanVar(value=True)
        self.skip_mhl_var = tk.BooleanVar(value=True)
        self.cb_size = ttk.Checkbutton(options_frame, text="Compare Size", variable=self.compare_size_var)
        self.cb_size.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.cb_date = ttk.Checkbutton(options_frame, text="Compare Modification Date", variable=self.compare_date_var)
        self.cb_date.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.cb_creation = ttk.Checkbutton(options_frame, text="Compare Creation Date", variable=self.compare_creation_var)
        self.cb_creation.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.cb_hidden = ttk.Checkbutton(options_frame, text="Skip Hidden Directories", variable=self.skip_hidden_var)
        self.cb_hidden.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.cb_mhl = ttk.Checkbutton(options_frame, text="Skip .mhl Files", variable=self.skip_mhl_var)
        self.cb_mhl.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Logging options
        self.fc_global_logging_enabled = tk.BooleanVar(value=False)
        self.fc_dest_logging_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Enable Logging", variable=self.fc_global_logging_enabled)\
            .grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Checkbutton(options_frame, text="Enable Logging Destination", variable=self.fc_dest_logging_enabled)\
            .grid(row=2, column=1, padx=5, pady=2, sticky="w")
        ttk.Button(options_frame, text="Log Directory", style="DIT.TButton", command=self.choose_log_directory)\
            .grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        # Progress bar and status label
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(pady=10)
        self.status_label = ttk.Label(self, text="Status: Idle", style="DIT.TLabel")
        self.status_label.pack(pady=5)
        
        # Button to start comparison
        self.compare_button = ttk.Button(self, text="Compare Files", style="DIT.TButton", command=self.compare_files)
        self.compare_button.pack(pady=5)
        
        # Scrolled text area for output
        self.text_area = scrolledtext.ScrolledText(self, width=80, height=15)
        self.text_area.pack(pady=5, fill="x", padx=10)
        
        # Bottom frame for clear status
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10)
        self.clear_status_button = ttk.Button(bottom_frame, text="Clear Status", style="DIT.TButton", command=self.clear_status)
        self.clear_status_button.pack(side=tk.LEFT, pady=5)
        self.append_text("File Comparator Tool Started.\n")
        self.append_text("Add drives, set a reference drive, and click 'Compare Files' to verify that your drives are identical.\n")
    
    def add_drive(self):
        # New method for individual drive selection.
        drive = filedialog.askdirectory(title="Select External Drive Directory")
        if drive:
            self.drive_paths.append(drive)
            self.listbox.insert(tk.END, drive)
            self.append_text(f"Added drive: {drive}\n")
    
    def add_all_drives(self):
        # Method to add all drives from /Volumes, remains unchanged.
        self.clear_drives()
        volumes_root = "/Volumes"
        if not os.path.exists(volumes_root):
            messagebox.showerror("Error", "Volumes directory not found.")
            return
        volumes = [d for d in os.listdir(volumes_root) if os.path.isdir(os.path.join(volumes_root, d))]
        filtered_volumes = []
        pattern = r'_(0*\d+[A-Za-z]?)$'
        for vol in volumes:
            if re.search(pattern, vol):
                filtered_volumes.append(vol)
        if not filtered_volumes:
            messagebox.showinfo("Add All Drives", "No external volumes with expected naming found.")
            return
        for vol in filtered_volumes:
            full_path = os.path.join(volumes_root, vol)
            self.drive_paths.append(full_path)
            self.listbox.insert(tk.END, full_path)
        self.append_text("All drives added.\n")
    
    def remove_drive(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            removed_drive = self.drive_paths.pop(index)
            self.listbox.delete(index)
            if self.reference_drive == removed_drive:
                self.reference_drive = None
                self.ref_label.config(text="Reference Drive: Not Set")
            self.append_text(f"Removed drive: {removed_drive}\n")
        else:
            messagebox.showwarning("Selection Error", "Please select a drive to remove.")
    
    def clear_status(self):
        self.text_area.delete("1.0", tk.END)
        self.progress_bar['value'] = 0
        self.update_status("Idle")
        self.append_text("Status cleared.\n")
    
    def choose_log_directory(self):
        directory = filedialog.askdirectory(title="Select Log Directory")
        if directory:
            self.log_directory = directory
            messagebox.showinfo("Log Directory", f"Log directory set to: {directory}")
    
    def clear_drives(self):
        self.drive_paths = []
        self.reference_drive = None
        self.listbox.delete(0, tk.END)
        self.ref_label.config(text="Reference Drive: Not Set")
        self.text_area.delete("1.0", tk.END)
        self.progress_bar['value'] = 0
        self.append_text("Drives cleared.\n")
    
    def set_reference(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.reference_drive = self.drive_paths[index]
            self.ref_label.config(text=f"Reference Drive: {self.reference_drive}")
        else:
            messagebox.showwarning("Selection Error", "Please select a drive from the list to set as reference.")
    
    def auto_reference(self):
        self.clear_drives()
        volumes_root = "/Volumes"
        if not os.path.exists(volumes_root):
            messagebox.showerror("Error", "Volumes directory not found.")
            return
        volumes = [d for d in os.listdir(volumes_root) if os.path.isdir(os.path.join(volumes_root, d))]
        filtered_volumes = []
        pattern = r'_(0*\d+[A-Za-z]?)$'
        for vol in volumes:
            if re.search(pattern, vol):
                filtered_volumes.append(vol)
        if not filtered_volumes:
            messagebox.showinfo("Auto Reference", "No external volumes with expected naming found.")
            return
        for vol in filtered_volumes:
            full_path = os.path.join(volumes_root, vol)
            self.drive_paths.append(full_path)
            self.listbox.insert(tk.END, full_path)
        reference_drive = None
        for vol in filtered_volumes:
            match = re.search(pattern, vol)
            if match:
                num_part = re.sub(r'[A-Za-z]', '', match.group(1))
                try:
                    if int(num_part) == 1:
                        reference_drive = os.path.join(volumes_root, vol)
                        break
                except Exception:
                    continue
        if reference_drive:
            self.reference_drive = reference_drive
            self.ref_label.config(text=f"Reference Drive: {reference_drive}")
        else:
            messagebox.showinfo("Auto Reference", "No volume with a reference naming found to set as reference.")
    
    def compare_files(self):
        if len(self.drive_paths) < 1:
            messagebox.showwarning("No Drives", "Please add at least one drive.")
            return
        self.text_area.delete("1.0", tk.END)
        self.progress_bar['value'] = 0
        self.status_label.config(text="Status: Starting comparison...")
        thread = threading.Thread(target=self.perform_comparison)
        thread.start()
    
    def perform_comparison(self):
        compare_size = self.compare_size_var.get()
        compare_date = self.compare_date_var.get()
        compare_creation = self.compare_creation_var.get()
        skip_hidden = self.skip_hidden_var.get()
        skip_mhl = self.skip_mhl_var.get()
        self.update_status("Scanning all drives...")
        drive_files = {}
        for drive in self.drive_paths:
            self.update_status(f"Scanning drive: {drive}")
            drive_files[drive] = scan_drive_attributes(
                drive, compare_size, compare_date, compare_creation, 
                skip_hidden=skip_hidden, skip_mhl=skip_mhl
            )
        all_keys = set()
        for files_dict in drive_files.values():
            all_keys.update(files_dict.keys())
        total_keys = len(all_keys)
        if total_keys == 0:
            self.append_text("No files or directories found on any drive.\n")
            self.update_status("Scan complete. No items found.")
            return
        self.update_status("Comparing items across all drives...")
        discrepancies = {}
        processed = 0
        ref_drive = self.reference_drive if self.reference_drive in drive_files else None
        for key in all_keys:
            processed += 1
            self.update_progress(processed, total_keys)
            ref_attr = drive_files[ref_drive].get(key) if ref_drive else None
            for drive, files_dict in drive_files.items():
                if key not in files_dict:
                    discrepancies.setdefault(drive, []).append(f"Missing item: {key}")
                else:
                    comp_attr = files_dict[key]
                    if ref_attr:
                        if ref_attr.get("type") != comp_attr.get("type"):
                            discrepancies.setdefault(drive, []).append(
                                f"Type mismatch for {key} (Ref: {ref_attr.get('type')}, {drive}: {comp_attr.get('type')})"
                            )
                        elif ref_attr.get("type") == "file":
                            messages = []
                            if compare_size and ref_attr.get('size') != comp_attr.get('size'):
                                messages.append(f"Size mismatch for {key} (Ref: {ref_attr.get('size')}, {drive}: {comp_attr.get('size')})")
                            if compare_date and ref_attr.get('mod_date') != comp_attr.get('mod_date'):
                                messages.append(f"Modification date mismatch for {key}")
                            if compare_creation and ref_attr.get('creation_date') != comp_attr.get('creation_date'):
                                messages.append(f"Creation date mismatch for {key}")
                            if messages:
                                discrepancies.setdefault(drive, []).extend(messages)
        if not discrepancies:
            self.append_text("All drives have the same items and attributes.\n")
            self.update_status("Comparison complete. No discrepancies found.")
            self.after(0, lambda: messagebox.showinfo("Comparison Result", "All drives match across all items."))
        else:
            result_text = ""
            for drive, messages in discrepancies.items():
                result_text += f"Discrepancies for drive: {drive}\n"
                for msg in messages:
                    result_text += "  " + msg + "\n"
                result_text += "\n"
            self.append_text(result_text)
            log_files = {}
            if self.fc_global_logging_enabled.get():
                log_files["global"] = self.write_global_log(discrepancies)
            if self.fc_dest_logging_enabled.get():
                log_files["destination"] = self.write_dest_logs(discrepancies)
            self.update_status("Comparison complete with discrepancies.")
            log_message = "Discrepancies found."
            if log_files:
                log_message += "\n\nLog files generated:"
                if "global" in log_files:
                    log_message += f"\n- Global log: {log_files['global']}"
                if "destination" in log_files and log_files["destination"]:
                    log_message += "\n- Destination logs:"
                    for drive, path in log_files["destination"].items():
                        log_message += f"\n  - {os.path.basename(drive)}: {path}"
            else:
                log_message += " No log files were generated (logging disabled)."
            self.after(0, lambda: messagebox.showwarning("Differences Found", log_message))
    
    def write_global_log(self, discrepancies):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.log_directory:
            log_filename = os.path.join(self.log_directory, f"File_Comparison_Log_{timestamp}.txt")
        else:
            log_filename = f"File_Comparison_Log_{timestamp}.txt"
        with open(log_filename, "w") as log_file:
            for drive, messages in discrepancies.items():
                log_file.write(f"Discrepancies for drive: {drive}\n")
                for msg in messages:
                    log_file.write("  " + msg + "\n")
                log_file.write("\n")
        return log_filename
    
    def write_dest_logs(self, discrepancies):
        dest_log_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for drive, messages in discrepancies.items():
            if messages:
                dest_log_path = os.path.join(drive, f"File_Comparison_Log_{timestamp}.txt")
                with open(dest_log_path, "w") as log_file:
                    log_file.write(f"Discrepancies for drive: {drive}\n")
                    for msg in messages:
                        log_file.write("  " + msg + "\n")
                    log_file.write("\n")
                dest_log_files[drive] = dest_log_path
        return dest_log_files
    
    def update_status(self, message):
        self.status_label.after(0, lambda: self.status_label.config(text=f"Status: {message}"))
    
    def append_text(self, text):
        self.text_area.after(0, lambda: self.text_area.insert(tk.END, text))
    
    def update_progress(self, value, maximum):
        self.progress_bar.after(0, lambda: self.progress_bar.config(value=value, maximum=maximum))