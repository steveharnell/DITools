import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, os, threading, re, queue, math
from datetime import datetime, timedelta
import json
# Note: For XXH64 checksum functionality, install the xxhash module: pip install xxhash

def transform_imported_settings(settings, current_module="sync"):
    """
    For this update we no longer modify the directory paths.
    The settings file will be named with a module-specific suffix when saved.
    """
    return settings

class NewSyncFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.out_queue = queue.Queue()
        self.global_logging_enabled = tk.BooleanVar(value=False)
        self.logging_dest_enabled = tk.BooleanVar(value=False)
        self.simultaneous_sync_enabled = tk.BooleanVar(value=True)
        self.fast_sync_enabled = tk.BooleanVar(value=True)  # Fast sync enabled by default
        self.use_higher_process_priority = tk.BooleanVar(value=True)
        self.use_native_cp = tk.BooleanVar(value=False)  # Use native cp command instead of rsync
        self.use_xxh64_checksum = tk.BooleanVar(value=False)  # XXH64 checksum option, disabled by default
        self.global_log_dir = tk.StringVar(value="")
        self.sync1_cancel_event = threading.Event()
        self.sync2_cancel_event = threading.Event()
        self.create_widgets()
        self.after(100, self.poll_queue)
    
    def format_size(self, size_bytes):
        """Format bytes to human-readable size"""
        if size_bytes == 0:
            return "0B"
        size_names = ("B", "KB", "MB", "GB", "TB", "PB")
        i = int(math.log(size_bytes, 1024))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def poll_queue(self):
        try:
            while True:
                line = self.out_queue.get_nowait()
                self.output_window.insert(tk.END, line)
                self.output_window.see(tk.END)
        except queue.Empty:
            pass
        self.after(100, self.poll_queue)

    def refresh_status_box(self, status_list, status_box):
        status_box.config(state=tk.NORMAL)
        status_box.delete("1.0", tk.END)
        for i, status in enumerate(status_list):
            if status:
                status_box.insert(tk.END, f"Dir {i + 1} {status}\n")
        status_box.config(state=tk.DISABLED)

    def update_sync_status(self, sync_status_list, index, new_status, status_box):
        sync_status_list[index] = new_status
        self.after(0, self.refresh_status_box, sync_status_list, status_box)

    def select_directory(self, entry):
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)

    def choose_global_log_directory(self):
        directory = filedialog.askdirectory(title="Select Global Log Directory")
        if directory:
            self.global_log_dir.set(directory)

    def run_sync_for_dest(self, source, dest, global_log_file, global_log_lock,
                          sync_status_list, index, status_box, cancel_event):
        import time
        
        # Ensure we start with a clean state
        if cancel_event.is_set():
            cancel_event.clear()
            
        self.out_queue.put(f"\nStarting sync: {source} -> {dest}\n")
        self.update_sync_status(sync_status_list, index, "In Progress", status_box)
        dest_log_file = None
        if self.logging_dest_enabled.get():
            log_path = os.path.join(dest, "rsync_log.txt")
            try:
                dest_log_file = open(log_path, "a")
                dest_log_file.write(f"--- Sync started: {source} -> {dest} ---\n")
            except Exception as e:
                self.out_queue.put(f"Destination Logging Error for {dest}: {e}\n")
        
        # If XXH64 checksum is enabled, check if xxhash module is available but don't disable
        xxhash_available = False
        xxh64_enabled = self.use_xxh64_checksum.get()
        
        if xxh64_enabled:
            try:
                # Try importing xxhash in a safer way that won't cause lasting issues
                xxhash_module = __import__('xxhash', fromlist=['*'])
                xxhash_available = True
                self.out_queue.put("XXH64 checksum enabled. This will verify file integrity but may slow down transfers.\n")
            except ImportError:
                self.out_queue.put("XXH64 checksum requested but xxhash Python module not found.\n")
                self.out_queue.put("Will attempt to use checksum verification with rsync directly.\n")
            except Exception as e:
                # Catch any other unexpected errors with the import
                self.out_queue.put(f"Error with xxhash module: {str(e)}\n")
                self.out_queue.put("Will use standard checksums instead.\n")
                
        # Make sure cancellation is properly checked early
        if cancel_event.is_set():
            self.update_sync_status(sync_status_list, index, "Cancelled", status_box)
            self.out_queue.put(f"Sync cancelled for {dest}\n")
            return
        
        self.out_queue.put("Calculating total size...\n")
        try:
            if os.name == 'posix':
                du_command = ["du", "-sk", source]
                du_process = subprocess.Popen(du_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                du_output, _ = du_process.communicate()
                if du_process.returncode == 0:
                    size_kb = int(du_output.split()[0])
                    total_size = size_kb * 1024
                    find_command = ["find", source, "-type", "f", "|", "wc", "-l"]
                    find_process = subprocess.Popen(" ".join(find_command), shell=True, stdout=subprocess.PIPE, text=True)
                    find_output, _ = find_process.communicate()
                    total_files = int(find_output.strip())
                    self.out_queue.put(f"Total transfer size: {self.format_size(total_size)} in approximately {total_files} files\n")
                else:
                    raise Exception("du command failed")
            else:
                size_command = ["rsync", "--stats", "--dry-run", "-a", source, dest]
                size_process = subprocess.Popen(size_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                total_size = 0
                total_files = 0
                for line in size_process.stdout:
                    if "Total file size:" in line:
                        size_match = re.search(r'Total file size: ([\d,]+) bytes', line)
                        if size_match:
                            total_size = int(size_match.group(1).replace(',', ''))
                    if "Number of files:" in line:
                        files_match = re.search(r'Number of files: ([\d,]+)', line)
                        if files_match:
                            total_files = int(files_match.group(1).replace(',', ''))
                size_process.wait()
                if total_size > 0:
                    self.out_queue.put(f"Total transfer size: {self.format_size(total_size)} in {total_files} files\n")
                else:
                    raise Exception("Could not parse rsync --stats output")
        except Exception as e:
            self.out_queue.put(f"Could not calculate total size accurately: {e}\n")
            self.out_queue.put("Will estimate progress based on individual file transfers instead.\n")
            total_size = 0
            total_files = 0
        
        if self.use_native_cp.get() and os.name == 'posix':
            command = ["cp", "-R", source, dest]
            self.out_queue.put("Using native CP command for maximum speed...\n")
            using_rsync = False
        else:
            using_rsync = True
            try:
                version_process = subprocess.Popen(["rsync", "--version"], stdout=subprocess.PIPE, text=True)
                version_output = version_process.stdout.readline()
                version_match = re.search(r'version (\d+)\.(\d+)\.(\d+)', version_output)
                if version_match:
                    major, minor, patch = map(int, version_match.groups())
                    
                    # Check if rsync supports XXH64 checksum (3.2.0+)
                    supports_xxh64 = (major > 3) or (major == 3 and minor >= 2)
                    
                    if major >= 3:
                        if self.fast_sync_enabled.get():
                            # Default fast sync mode
                            command = ["rsync", "-a", "--progress", "--no-checksum", "--no-times", 
                                      "--whole-file", "--block-size=32768", source, dest]
                            self.out_queue.put("Using fast sync mode (optimized for speed) with modern rsync...\n")
                            
                            # If XXH64 is enabled, modify command to use checksums
                            if xxh64_enabled:
                                if supports_xxh64:
                                    # For rsync 3.2.0+, use xxh64 checksum
                                    command = ["rsync", "-a", "--progress", "--checksum", "--checksum-choice=xxh64", 
                                              "--whole-file", "--block-size=32768", source, dest]
                                    self.out_queue.put("Using XXH64 BE checksum (rsync 3.2.0+) for data integrity verification...\n")
                                else:
                                    # For older rsync, fall back to standard checksum
                                    command = ["rsync", "-a", "--progress", "--checksum", 
                                              "--whole-file", "--block-size=32768", source, dest]
                                    self.out_queue.put("Using standard MD5 checksum for data integrity verification (rsync < 3.2.0)...\n")
                        else:
                            # Default standard sync mode
                            command = ["rsync", "-a", "--progress", source, dest]
                            self.out_queue.put("Using standard sync mode (thorough verification) with modern rsync...\n")
                            
                            # If XXH64 is enabled, add the appropriate checksum option
                            if xxh64_enabled:
                                if supports_xxh64:
                                    # For rsync 3.2.0+, use xxh64 checksum
                                    command = ["rsync", "-a", "--progress", "--checksum", "--checksum-choice=xxh64", source, dest]
                                    self.out_queue.put("Using XXH64 BE checksum (rsync 3.2.0+) for data integrity verification...\n")
                                else:
                                    # For older rsync, fall back to standard checksum
                                    command = ["rsync", "-a", "--progress", "--checksum", source, dest]
                                    self.out_queue.put("Using standard MD5 checksum for data integrity verification (rsync < 3.2.0)...\n")
                    else:
                        # Older rsync (version < 3)
                        if self.fast_sync_enabled.get():
                            command = ["rsync", "-rltDW", "--progress", source, dest]
                            self.out_queue.put("Using maximum performance mode for older rsync...\n")
                            self.out_queue.put("Note: This optimized mode may skip some metadata but maximizes transfer speed.\n")
                            
                            # If XXH64 is enabled for older rsync, fall back to standard checksum
                            if xxh64_enabled:
                                command = ["rsync", "-a", "--progress", "--checksum", source, dest]
                                self.out_queue.put("Using standard checksum for data integrity verification (rsync < 3.0)...\n")
                        else:
                            command = ["rsync", "-a", "--progress", source, dest]
                            self.out_queue.put("Using standard sync mode with older rsync...\n")
                            
                            # If XXH64 is enabled for older rsync, add standard checksum option
                            if xxh64_enabled:
                                command = ["rsync", "-a", "--progress", "--checksum", source, dest]
                                self.out_queue.put("Using standard checksum for data integrity verification (rsync < 3.0)...\n")
                else:
                    command = ["rsync", "-a", "--progress", source, dest]
                    self.out_queue.put("Using basic rsync command (compatible with all versions)...\n")
            except Exception as e:
                self.out_queue.put(f"Error detecting rsync version: {e}. Using basic command...\n")
                command = ["rsync", "-a", "--progress", source, dest]
        
        if self.use_higher_process_priority.get() and os.name == 'posix':
            try:
                test_process = subprocess.run(["nice", "-n", "-10", "echo", "test"], 
                                             capture_output=True, text=True, check=False)
                if test_process.returncode == 0:
                    command = ["nice", "-n", "-10"] + command
                    self.out_queue.put("Using higher process priority...\n")
                else:
                    command = ["nice", "-n", "10"] + command
                    self.out_queue.put("Using standard process priority (requires admin privileges for high priority)...\n")
            except Exception as e:
                self.out_queue.put(f"Could not adjust process priority: {e}. Continuing without priority adjustment.\n")
        
        start_time = time.time()
        bytes_transferred = 0
        last_update_time = start_time
        
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            if self.use_native_cp.get() and os.name == 'posix':
                self.update_sync_status(sync_status_list, index, "In Progress - Using native CP command", status_box)
                while process.poll() is None:
                    if cancel_event.is_set():
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        self.update_sync_status(sync_status_list, index, "Cancelled", status_box)
                        self.out_queue.put(f"Sync cancelled for {dest}\n")
                        break
                    if total_size > 0:
                        try:
                            current_time = time.time()
                            if current_time - last_update_time >= 1.0:
                                last_update_time = current_time
                                if os.path.exists(dest):
                                    du_dest_cmd = ["du", "-sk", dest]
                                    du_dest_process = subprocess.Popen(du_dest_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                                    du_dest_output, _ = du_dest_process.communicate()
                                    if du_dest_process.returncode == 0:
                                        dest_size_kb = int(du_dest_output.split()[0])
                                        dest_size = dest_size_kb * 1024
                                        elapsed = current_time - start_time
                                        speed_bps = dest_size / elapsed if elapsed > 0 else 0
                                        progress = min(int((dest_size / total_size) * 100), 99)
                                        speed_str = self.format_size(speed_bps) + "/s"
                                        if speed_bps > 0 and progress < 99:
                                            remaining_bytes = total_size - dest_size
                                            eta_seconds = remaining_bytes / speed_bps
                                            eta_str = str(timedelta(seconds=int(eta_seconds)))
                                            status_msg = f"In Progress ({progress}%) - {self.format_size(dest_size)}/{self.format_size(total_size)} - {speed_str} - ETA: {eta_str}"
                                        else:
                                            status_msg = f"In Progress ({progress}%) - {self.format_size(dest_size)}/{self.format_size(total_size)} - {speed_str}"
                                        self.update_sync_status(sync_status_list, index, status_msg, status_box)
                        except Exception as e:
                            pass
                    time.sleep(0.5)
                output, _ = process.communicate()
                if output:
                    self.out_queue.put(output)
                if process.returncode == 0:
                    self.update_sync_status(sync_status_list, index, "Completed", status_box)
                    self.out_queue.put(f"Sync completed for {dest}\n")
                else:
                    self.update_sync_status(sync_status_list, index, f"Failed (code {process.returncode})", status_box)
                    self.out_queue.put(f"Sync failed for {dest} with code {process.returncode}\n")
            else:
                while True:
                    if cancel_event.is_set():
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        self.update_sync_status(sync_status_list, index, "Cancelled", status_box)
                        self.out_queue.put(f"Sync cancelled for {dest}\n")
                        break
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        self.out_queue.put(line)
                    sent_match = re.search(r'sent (\d+,?\d*) bytes', line)
                    if sent_match and total_size > 0:
                        sent_bytes = int(sent_match.group(1).replace(',', ''))
                        if sent_bytes > bytes_transferred:
                            bytes_transferred = sent_bytes
                            current_time = time.time()
                            if current_time - last_update_time >= 1.0:
                                last_update_time = current_time
                                elapsed = current_time - start_time
                                overall_percentage = min(int((bytes_transferred / total_size) * 100), 100)
                                if elapsed > 0:
                                    speed_bps = bytes_transferred / elapsed
                                    speed_str = self.format_size(speed_bps) + "/s"
                                    if speed_bps > 0 and overall_percentage < 100:
                                        remaining_bytes = total_size - bytes_transferred
                                        eta_seconds = remaining_bytes / speed_bps
                                        eta_str = str(timedelta(seconds=int(eta_seconds)))
                                        status_msg = f"In Progress ({overall_percentage}%) - {self.format_size(bytes_transferred)}/{self.format_size(total_size)} - {speed_str} - ETA: {eta_str}"
                                    else:
                                        status_msg = f"In Progress ({overall_percentage}%) - {self.format_size(bytes_transferred)}/{self.format_size(total_size)} - {speed_str}"
                                else:
                                    status_msg = f"In Progress ({overall_percentage}%) - {self.format_size(bytes_transferred)}/{self.format_size(total_size)}"
                                self.update_sync_status(sync_status_list, index, status_msg, status_box)
                    match = re.search(r'(\d+)%', line)
                    if match:
                        file_progress = int(match.group(1))
                        file_match = re.search(r'([^\s/]+)$', line.strip())
                        current_file = file_match.group(1) if file_match else "current file"
                        if total_size > 0 and bytes_transferred > 0:
                            overall_percentage = min(int((bytes_transferred / total_size) * 100), 100)
                            status_msg = f"Total: {overall_percentage}% - File: {file_progress}% - {current_file}"
                        else:
                            status_msg = f"File: {file_progress}% - {current_file}"
                        self.update_sync_status(sync_status_list, index, status_msg, status_box)
                    
                    # Write to log files if enabled
                    if global_log_file and global_log_lock:
                        with global_log_lock:
                            global_log_file.write(line)
                            global_log_file.flush()
                    if dest_log_file:
                        dest_log_file.write(line)
                        dest_log_file.flush()
            if not cancel_event.is_set():
                self.update_sync_status(sync_status_list, index, "Completed", status_box)
                self.out_queue.put(f"Sync completed for {dest}\n")
            if dest_log_file:
                dest_log_file.write(f"--- Sync finished for {dest} ---\n\n")
                dest_log_file.close()
            if global_log_file and global_log_lock:
                with global_log_lock:
                    global_log_file.write(f"--- Global Sync Finished for source: {source} ---\n")
                    global_log_file.flush()
        except Exception as e:
            self.out_queue.put(f"Execution Error on {dest}: {e}\n")
            self.update_sync_status(sync_status_list, index, "Failed", status_box)

    def run_sync(self, source, dest_list, sync_status_list, status_box, cancel_event):
        # First, ensure we start with a clean cancel event
        cancel_event.clear()
        
        if not source:
            messagebox.showerror("Error", "Source directory must be selected.")
            return
        for i in range(len(sync_status_list)):
            sync_status_list[i] = ""
        valid_dests = []
        for i, dest in enumerate(dest_list):
            if dest.strip():
                sync_status_list[i] = "Pending"
                valid_dests.append(dest)
        if not valid_dests:
            messagebox.showerror("Error", "At least one destination directory must be selected.")
            return
        self.refresh_status_box(sync_status_list, status_box)
        global_log_file = None
        global_log_lock = None
        if self.global_logging_enabled.get():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if self.global_log_dir.get():
                    log_path = os.path.join(self.global_log_dir.get(), f"rsync_log_{timestamp}.txt")
                else:
                    log_path = f"rsync_log_{timestamp}.txt"
                global_log_file = open(log_path, "w")
                global_log_file.write(f"--- Global Sync Started for source: {source} ---\n")
                global_log_lock = threading.Lock()
            except Exception as e:
                messagebox.showerror("Global Logging Error", f"Failed to open global log file: {e}")
                global_log_file = None
        if self.simultaneous_sync_enabled.get():
            threads = []
            for i, dest in enumerate(dest_list):
                if not dest.strip():
                    continue
                t = threading.Thread(target=self.run_sync_for_dest,
                                     args=(source, dest, global_log_file, global_log_lock,
                                           sync_status_list, i, status_box, cancel_event))
                t.daemon = True
                t.start()
                threads.append(t)

            def wait_for_threads():
                for t in threads:
                    t.join()
                if global_log_file:
                    with global_log_lock:
                        global_log_file.write(f"--- Global Sync Finished for source: {source} ---\n\n")
                        global_log_file.close()
                        self.out_queue.put("Global sync complete, log file closed.\n")

            wait_thread = threading.Thread(target=wait_for_threads)
            wait_thread.daemon = True
            wait_thread.start()
        else:
            for i, dest in enumerate(dest_list):
                if not dest.strip():
                    continue
                if cancel_event.is_set():
                    self.out_queue.put(f"Skipping sync for {dest} due to cancellation.\n")
                    self.update_sync_status(sync_status_list, i, "Skipped", status_box)
                    continue
                self.run_sync_for_dest(source, dest, global_log_file, global_log_lock,
                                       sync_status_list, i, status_box, cancel_event)
            if global_log_file and not cancel_event.is_set():
                global_log_file.write(f"--- Global Sync Finished for source: {source} ---\n\n")
                global_log_file.close()
                self.out_queue.put("Global sync complete, log file closed.\n")
            elif global_log_file:
                global_log_file.write(f"--- Global Sync Cancelled for source: {source} ---\n\n")
                global_log_file.close()
                self.out_queue.put("Global sync cancelled, log file closed.\n")

    def run_sync1(self):
        self.sync1_button.config(state=tk.DISABLED)
        self.sync1_cancel_event = threading.Event()
        source = self.sync1_source_entry.get().strip()
        dest_list = [entry.get().strip() for entry in self.sync1_dest_entries]

        def run_sync_thread():
            try:
                self.run_sync(source, dest_list, self.sync1_statuses, self.sync1_status_box, self.sync1_cancel_event)
            except Exception as e:
                self.out_queue.put(f"\nError during sync: {str(e)}\n")
                for i in range(len(self.sync1_statuses)):
                    if self.sync1_statuses[i] == "Pending" or self.sync1_statuses[i].startswith("In Progress"):
                        self.sync1_statuses[i] = "Failed (Error)"
                self.refresh_status_box(self.sync1_statuses, self.sync1_status_box)
            finally:
                # Always re-enable the button, no matter what happened
                self.after(0, lambda: self.sync1_button.config(state=tk.NORMAL))

        threading.Thread(target=run_sync_thread, daemon=True).start()

    def run_sync2(self):
        self.sync2_button.config(state=tk.DISABLED)
        self.sync2_cancel_event = threading.Event()
        source = self.sync2_source_entry.get().strip()
        dest_list = [entry.get().strip() for entry in self.sync2_dest_entries]

        def run_sync_thread():
            try:
                self.run_sync(source, dest_list, self.sync2_statuses, self.sync2_status_box, self.sync2_cancel_event)
            except Exception as e:
                self.out_queue.put(f"\nError during sync: {str(e)}\n")
                for i in range(len(self.sync2_statuses)):
                    if self.sync2_statuses[i] == "Pending" or self.sync2_statuses[i].startswith("In Progress"):
                        self.sync2_statuses[i] = "Failed (Error)"
                self.refresh_status_box(self.sync2_statuses, self.sync2_status_box)
            finally:
                # Always re-enable the button, no matter what happened
                self.after(0, lambda: self.sync2_button.config(state=tk.NORMAL))

        threading.Thread(target=run_sync_thread, daemon=True).start()

    def cancel_sync1(self):
        if self.sync1_cancel_event:
            self.sync1_cancel_event.set()
            self.out_queue.put("\nSync Option 1 cancellation requested.\n")
            # Enable button immediately to allow user to try again
            self.sync1_button.config(state=tk.NORMAL)

    def cancel_sync2(self):
        if self.sync2_cancel_event:
            self.sync2_cancel_event.set()
            self.out_queue.put("\nSync Option 2 cancellation requested.\n")
            # Enable button immediately to allow user to try again
            self.sync2_button.config(state=tk.NORMAL)

    def clear_directories(self):
        self.sync1_source_entry.delete(0, tk.END)
        for entry in self.sync1_dest_entries:
            entry.delete(0, tk.END)
        self.sync2_source_entry.delete(0, tk.END)
        for entry in self.sync2_dest_entries:
            entry.delete(0, tk.END)

    def clear_status(self):
        self.output_window.delete("1.0", tk.END)

    # --- Settings Controls functions for Sync ---
    def validate_settings(self, settings):
        errors = []
        # For Sync settings, directory fields are optional.
        return errors

    def import_settings(self):
        filename = filedialog.askopenfilename(
            title="Select Settings File",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                settings = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read settings file: {e}")
            return

        # Check if this is a sync settings file
        if settings.get("module") != "sync":
            messagebox.showerror("Settings Error", "The selected file is not a valid sync settings file.")
            return

        errors = self.validate_settings(settings)
        if errors:
            messagebox.showerror("Settings Error", "The following errors were found:\n" + "\n".join(errors))
            return

        # No transformation of directories needed in this update.
        settings = transform_imported_settings(settings, current_module="sync")

        self.global_logging_enabled.set(settings.get("global_logging_enabled", False))
        self.logging_dest_enabled.set(settings.get("logging_dest_enabled", False))
        self.simultaneous_sync_enabled.set(settings.get("simultaneous_sync_enabled", True))
        self.fast_sync_enabled.set(settings.get("fast_sync_enabled", True))
        self.use_higher_process_priority.set(settings.get("use_higher_process_priority", True))
        self.use_native_cp.set(settings.get("use_native_cp", False))
        self.use_xxh64_checksum.set(settings.get("use_xxh64_checksum", False))
        self.global_log_dir.set(settings.get("global_log_dir", ""))

        # Restore directory information
        sync1_source = settings.get("sync1_source", "")
        self.sync1_source_entry.delete(0, tk.END)
        self.sync1_source_entry.insert(0, sync1_source)

        sync1_destinations = settings.get("sync1_destinations", [])
        for i, entry in enumerate(self.sync1_dest_entries):
            entry.delete(0, tk.END)
            if i < len(sync1_destinations):
                entry.insert(0, sync1_destinations[i])

        sync2_source = settings.get("sync2_source", "")
        self.sync2_source_entry.delete(0, tk.END)
        self.sync2_source_entry.insert(0, sync2_source)

        sync2_destinations = settings.get("sync2_destinations", [])
        for i, entry in enumerate(self.sync2_dest_entries):
            entry.delete(0, tk.END)
            if i < len(sync2_destinations):
                entry.insert(0, sync2_destinations[i])

        messagebox.showinfo("Import Settings", "Settings imported successfully.")

    def save_settings(self):
        settings = {
            "module": "sync",
            "global_logging_enabled": self.global_logging_enabled.get(),
            "logging_dest_enabled": self.logging_dest_enabled.get(),
            "simultaneous_sync_enabled": self.simultaneous_sync_enabled.get(),
            "fast_sync_enabled": self.fast_sync_enabled.get(),
            "use_higher_process_priority": self.use_higher_process_priority.get(),
            "use_native_cp": self.use_native_cp.get(),
            "use_xxh64_checksum": self.use_xxh64_checksum.get(),
            "global_log_dir": self.global_log_dir.get(),
            # Include directory information
            "sync1_source": self.sync1_source_entry.get().strip(),
            "sync1_destinations": [entry.get().strip() for entry in self.sync1_dest_entries],
            "sync2_source": self.sync2_source_entry.get().strip(),
            "sync2_destinations": [entry.get().strip() for entry in self.sync2_dest_entries]
        }
        errors = self.validate_settings(settings)
        if errors:
            messagebox.showerror("Settings Error", "Cannot save due to the following errors:\n" + "\n".join(errors))
            return
        filename = filedialog.asksaveasfilename(
            title="Save Settings File",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filename:
            return
        
        # Ensure the file name includes the module suffix.
        if filename.endswith(".json"):
            base = filename[:-5]
            if not base.endswith("_sync"):
                filename = base + "_sync.json"
        else:
            if not filename.endswith("_sync"):
                filename = filename + "_sync"
        
        try:
            with open(filename, "w") as f:
                json.dump(settings, f, indent=4)
            messagebox.showinfo("Save Settings", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings file: {e}")

    def show_template(self):
        sample = {
            "module": "sync",
            "global_logging_enabled": True,
            "logging_dest_enabled": True,
            "simultaneous_sync_enabled": True,
            "fast_sync_enabled": True,
            "use_higher_process_priority": True,
            "use_native_cp": False,
            "use_xxh64_checksum": False,
            "global_log_dir": "/path/to/global/log/dir",
            "sync1_source": "/path/to/sync1/source",
            "sync1_destinations": ["/path/to/sync1/dest1", "/path/to/sync1/dest2", "", ""],
            "sync2_source": "/path/to/sync2/source",
            "sync2_destinations": ["/path/to/sync2/dest1", "/path/to/sync2/dest2", "", ""]
        }
        sample_text = json.dumps(sample, indent=4)
        
        # Create a modal dialog window
        template_win = tk.Toplevel(self)
        template_win.title("Sample Settings Template")
        template_win.transient(self)  # Make window modal
        template_win.grab_set()  # Make window modal
        template_win.focus_set()  # Take focus
        
        # Calculate position - center the window
        window_width = 500
        window_height = 400
        position_right = int(template_win.winfo_screenwidth()/2 - window_width/2)
        position_down = int(template_win.winfo_screenheight()/2 - window_height/2)
        template_win.geometry(f"{window_width}x{window_height}+{position_right}+{position_down}")
        
        # Make the window resizable and set minimum size
        template_win.minsize(400, 300)
        
        # Add the text widget with scrollbars
        frame = ttk.Frame(template_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbars
        scrollbar_y = ttk.Scrollbar(frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create text widget with scrollbars
        text_widget = tk.Text(frame, wrap="none", width=60, height=20,
                            yscrollcommand=scrollbar_y.set,
                            xscrollcommand=scrollbar_x.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        scrollbar_y.config(command=text_widget.yview)
        scrollbar_x.config(command=text_widget.xview)
        
        # Insert the text and disable editing
        text_widget.insert("1.0", sample_text)
        text_widget.config(state="disabled")
        
        # Add close button at the bottom
        close_btn = ttk.Button(template_win, text="Close", style="DIT.TButton", 
                              command=template_win.destroy)
        close_btn.pack(pady=10)
        
        # Wait for the window to be closed before returning
        self.wait_window(template_win)

    def create_widgets(self):
        # Sync Option 1 Frame
        sync1_frame = ttk.LabelFrame(self, text="Sync Option 1", padding=4)
        sync1_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(sync1_frame, text="Source Directory:", style="DIT.TLabel").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.sync1_source_entry = ttk.Entry(sync1_frame, width=50)
        self.sync1_source_entry.grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(sync1_frame, text="Select Source", style="DIT.TButton", command=lambda: self.select_directory(self.sync1_source_entry)).grid(row=0, column=2, padx=2, pady=2)
        self.sync1_dest_entries = []
        for i in range(4):
            ttk.Label(sync1_frame, text=f"Destination Directory {i + 1}:", style="DIT.TLabel").grid(row=i + 1, column=0, sticky="e", padx=2, pady=2)
            entry = ttk.Entry(sync1_frame, width=50)
            entry.grid(row=i + 1, column=1, padx=2, pady=2)
            self.sync1_dest_entries.append(entry)
            ttk.Button(sync1_frame, text="Select Destination", style="DIT.TButton", command=lambda e=entry: self.select_directory(e)).grid(row=i + 1, column=2, padx=2, pady=2)
        button_frame1 = ttk.Frame(sync1_frame)
        button_frame1.grid(row=5, column=0, columnspan=3, padx=2, pady=4, sticky="w")
        self.sync1_button = ttk.Button(button_frame1, text="Sync", style="DIT.TButton", command=self.run_sync1)
        self.sync1_button.pack(side="left", padx=2)
        ttk.Button(button_frame1, text="Cancel Sync", style="DIT.TButton", command=self.cancel_sync1).pack(side="left", padx=2)
        status_frame1 = ttk.Frame(button_frame1)
        status_frame1.pack(side="left", padx=10)
        ttk.Label(status_frame1, text="Status:", style="DIT.TLabel").pack(side="left")
        self.sync1_status_box = tk.Text(status_frame1, height=4, width=40, borderwidth=2, relief="sunken")
        self.sync1_status_box.pack(side="left", padx=(5, 0))
        self.sync1_status_box.config(state=tk.DISABLED)
        self.sync1_statuses = [""] * 4

        # Sync Option 2 Frame
        sync2_frame = ttk.LabelFrame(self, text="Sync Option 2", padding=4)
        sync2_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(sync2_frame, text="Source Directory:", style="DIT.TLabel").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.sync2_source_entry = ttk.Entry(sync2_frame, width=50)
        self.sync2_source_entry.grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(sync2_frame, text="Select Source", style="DIT.TButton", command=lambda: self.select_directory(self.sync2_source_entry)).grid(row=0, column=2, padx=2, pady=2)
        self.sync2_dest_entries = []
        for i in range(4):
            ttk.Label(sync2_frame, text=f"Destination Directory {i + 1}:", style="DIT.TLabel").grid(row=i + 1, column=0, sticky="e", padx=2, pady=2)
            entry = ttk.Entry(sync2_frame, width=50)
            entry.grid(row=i + 1, column=1, padx=2, pady=2)
            self.sync2_dest_entries.append(entry)
            ttk.Button(sync2_frame, text="Select Destination", style="DIT.TButton", command=lambda e=entry: self.select_directory(e)).grid(row=i + 1, column=2, padx=2, pady=2)
        button_frame2 = ttk.Frame(sync2_frame)
        button_frame2.grid(row=5, column=0, columnspan=3, padx=2, pady=4, sticky="w")
        self.sync2_button = ttk.Button(button_frame2, text="Sync", style="DIT.TButton", command=self.run_sync2)
        self.sync2_button.pack(side="left", padx=2)
        ttk.Button(button_frame2, text="Cancel Sync", style="DIT.TButton", command=self.cancel_sync2).pack(side="left", padx=2)
        status_frame2 = ttk.Frame(button_frame2)
        status_frame2.pack(side="left", padx=10)
        ttk.Label(status_frame2, text="Status:", style="DIT.TLabel").pack(side="left")
        self.sync2_status_box = tk.Text(status_frame2, height=4, width=40, borderwidth=2, relief="sunken")
        self.sync2_status_box.pack(side="left", padx=(5, 0))
        self.sync2_status_box.config(state=tk.DISABLED)
        self.sync2_statuses = [""] * 4

        # Global Options
        checkbox_frame = ttk.Frame(self)
        checkbox_frame.pack(padx=10, pady=5, anchor="w")
        ttk.Checkbutton(checkbox_frame, text="Enable Logging", variable=self.global_logging_enabled, style="DIT.TCheckbutton").pack(side="left", padx=4)
        ttk.Checkbutton(checkbox_frame, text="Enable Logging Destination", variable=self.logging_dest_enabled, style="DIT.TCheckbutton").pack(side="left", padx=4)
        ttk.Checkbutton(checkbox_frame, text="Sync Volumes Simultaneously", variable=self.simultaneous_sync_enabled, style="DIT.TCheckbutton").pack(side="left", padx=4)
        
        # Performance Options
        performance_frame = ttk.Frame(self)
        performance_frame.pack(padx=10, pady=5, anchor="w")
        ttk.Checkbutton(performance_frame, text="Fast Sync Mode (Speed over Verification)", variable=self.fast_sync_enabled, style="DIT.TCheckbutton").pack(side="left", padx=4)
        ttk.Checkbutton(performance_frame, text="Use Higher Process Priority", variable=self.use_higher_process_priority, style="DIT.TCheckbutton").pack(side="left", padx=4)
        ttk.Checkbutton(performance_frame, text="Use Native CP Command (macOS Only)", variable=self.use_native_cp, style="DIT.TCheckbutton").pack(side="left", padx=4)
        
        # Create a new frame for the XXH64 option and its warning
        xxh64_frame = ttk.Frame(self)
        xxh64_frame.pack(padx=10, pady=2, anchor="w")
        ttk.Checkbutton(xxh64_frame, text="Use File Checksum Verification (XXH64 BE if available)", variable=self.use_xxh64_checksum, style="DIT.TCheckbutton").pack(side="left", padx=4)
        
        # Log Directory
        log_dir_frame = ttk.Frame(self)
        log_dir_frame.pack(padx=10, pady=5, anchor="w")
        ttk.Button(log_dir_frame, text="Log Directory", style="DIT.TButton", command=self.choose_global_log_directory).pack(side="left", padx=4)
        ttk.Label(log_dir_frame, textvariable=self.global_log_dir, width=50, anchor="w", style="DIT.TLabel").pack(side="left", padx=4)
        
        # Settings Controls Frame
        settings_frame = ttk.LabelFrame(self, text="Settings Controls", padding=5)
        settings_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(settings_frame, text="Import Settings", style="DIT.TButton", command=self.import_settings).pack(side="left", padx=2)
        ttk.Button(settings_frame, text="Save Settings", style="DIT.TButton", command=self.save_settings).pack(side="left", padx=2)
        ttk.Button(settings_frame, text="Show Template", style="DIT.TButton", command=self.show_template).pack(side="left", padx=2)
        
        self.output_window = tk.Text(self, height=11, width=100, borderwidth=2, relief="sunken")
        self.output_window.pack(padx=10, pady=10, fill="both", expand=True)

        # Bottom Frame with Clear Status and Clear Directories buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(bottom_frame, text="Clear Status", style="DIT.TButton", command=self.clear_status).pack(side="left")
        ttk.Button(bottom_frame, text="Clear Directories", style="DIT.TButton", command=self.clear_directories).pack(side="right")

        self.output_window.insert(tk.END, "Sync Tool Started.\n")
        self.output_window.insert(tk.END, "Select directories and click Sync to begin.\n")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sync")
    sync_frame = NewSyncFrame(root)
    sync_frame.pack(fill="both", expand=True)
    root.mainloop()