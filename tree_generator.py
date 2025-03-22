import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from datetime import datetime
import os
import threading

class TreeGeneratorFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        if os.name == 'nt':
            default_dir = "C:\\"
        else:
            default_dir = "/"
        self.directories = [default_dir] * 4
        self.active_dir_index = 0
        self.skip_hidden = tk.BooleanVar(value=True)
        self.radio_var = tk.IntVar(value=0)
        self.create_widgets()
        self.log("Tree Generator Tool Started. Select a directory to generate a text-based tree inventory of your files.")
        self.update_all_dir_labels()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Directory Selections
        dir_selection_frame = ttk.LabelFrame(main_frame, text="Directory Selections", padding="5")
        dir_selection_frame.pack(fill=tk.X, pady=5)
        self.dir_labels = []
        for i in range(4):
            frame = ttk.Frame(dir_selection_frame, padding="2")
            frame.pack(fill=tk.X, pady=2)
            radio = ttk.Radiobutton(frame, text=f"Directory {i+1}", variable=self.radio_var, value=i,
                                    command=lambda idx=i: self.set_active_directory(idx))
            radio.pack(side=tk.LEFT, padx=5)
            label = ttk.Label(frame, text=self.directories[i], width=60, style="DIT.TLabel")
            label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            btn = ttk.Button(frame, text="Select", style="DIT.TButton", command=lambda idx=i: self.select_directory(idx))
            btn.pack(side=tk.RIGHT, padx=5)
            self.dir_labels.append(label)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        skip_check = ttk.Checkbutton(options_frame, text="Skip Hidden Files/Directories", variable=self.skip_hidden, style="DIT.TCheckbutton")
        skip_check.pack(anchor=tk.W, padx=5)
        
        # Action Buttons
        btn_frame = ttk.Frame(main_frame, padding="5")
        btn_frame.pack(fill=tk.X, pady=5)
        gen_btn = ttk.Button(btn_frame, text="Generate Tree", style="DIT.TButton", command=self.generate_tree)
        gen_btn.pack(side=tk.LEFT, padx=5)
        list_btn = ttk.Button(btn_frame, text="List Directory", style="DIT.TButton", command=self.log_directory)
        list_btn.pack(side=tk.LEFT, padx=5)
        save_btn = ttk.Button(btn_frame, text="Save Log To...", style="DIT.TButton", command=self.save_log)
        save_btn.pack(side=tk.LEFT, padx=5)
        clear_btn = ttk.Button(btn_frame, text="Clear Status", style="DIT.TButton", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Log Area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def update_all_dir_labels(self):
        for i, directory in enumerate(self.directories):
            self.dir_labels[i].config(text=directory)
    
    def set_active_directory(self, index):
        self.active_dir_index = index
        self.log(f"Active directory set to Directory {index+1}: {self.directories[index]}")
    
    def select_directory(self, index):
        directory = filedialog.askdirectory(initialdir=self.directories[index])
        if directory:
            self.directories[index] = directory
            self.dir_labels[index].config(text=directory)
            self.log(f"Directory {index+1} selected: {directory}")
            self.radio_var.set(index)
            self.set_active_directory(index)
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def log_directory(self):
        active_dir = self.directories[self.active_dir_index]
        self.log(f"Contents of Directory {self.active_dir_index+1}: {active_dir}")
        try:
            items = os.listdir(active_dir)
            for item in sorted(items):
                if self.skip_hidden.get() and item.startswith('.'):
                    continue
                full_path = os.path.join(active_dir, item)
                if os.path.isdir(full_path):
                    self.log(f"  [DIR] {item}")
                else:
                    size = self.format_size(os.path.getsize(full_path))
                    self.log(f"  [FILE] {item} ({size})")
        except Exception as e:
            self.log(f"Error listing directory: {str(e)}")
    
    def save_log(self):
        active_dir = self.directories[self.active_dir_index]
        file_path = filedialog.asksaveasfilename(
            initialdir=active_dir,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"directory_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get("1.0", tk.END))
                self.log(f"Log saved to: {file_path}")
            except Exception as e:
                self.log(f"Error saving log: {str(e)}")
    
    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
        self.log("Status cleared")
    
    def generate_tree(self):
        active_dir = self.directories[self.active_dir_index]
        if not os.path.exists(active_dir):
            self.log(f"Error: Directory doesn't exist: {active_dir}")
            return
        dir_name = os.path.basename(active_dir)
        dir_name_underscored = dir_name.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y_%m_%d_at_%H_%M_%S")
        output_filename = f"INDEX_OF_{dir_name_underscored}_{timestamp}.txt"
        output_path = os.path.join(active_dir, output_filename)
        self.log(f"Generating directory tree for: {active_dir}")
        self.log(f"Output file will be saved as: {output_filename}")
        threading.Thread(target=self._generate_tree_thread, args=(active_dir, output_path)).start()
    
    def _generate_tree_thread(self, start_path, output_file):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{start_path}\n")
            self._generate_tree_recursive(start_path, output_file, level=0)
            self.after(0, lambda: self.log(f"Tree generation complete: {output_file}"))
        except Exception as e:
            self.after(0, lambda: self.log(f"Error generating tree: {str(e)}"))
    
    def _generate_tree_recursive(self, path, output_file, level=0):
        try:
            items = os.listdir(path)
            items.sort()
            for i, item in enumerate(items):
                if self.skip_hidden.get() and item.startswith('.'):
                    continue
                item_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                prefix = ('│   ' * (level - 1) + ('└── ' if is_last else '├── ')) if level > 0 else ''
                with open(output_file, 'a', encoding='utf-8') as f:
                    if os.path.isfile(item_path):
                        try:
                            size = os.path.getsize(item_path)
                            size_str = self.format_size(size)
                            f.write(f"{prefix}{item} [{size_str}]\n")
                        except (OSError, FileNotFoundError):
                            f.write(f"{prefix}{item} [access denied]\n")
                    else:
                        try:
                            dir_size = self.get_dir_size(item_path)
                            size_str = self.format_size(dir_size)
                            f.write(f"{prefix}{item} [{size_str}]\n")
                            self._generate_tree_recursive(item_path, output_file, level + 1)
                        except (OSError, FileNotFoundError):
                            f.write(f"{prefix}{item} [access denied]\n")
        except (OSError, FileNotFoundError) as e:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{' ' * 4 * level}[Error accessing directory: {str(e)}]\n")
    
    def get_dir_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            if self.skip_hidden.get():
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
                filenames = [f for f in filenames if not f.startswith('.')]
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
        return total_size
    
    def format_size(self, size_in_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} PB"