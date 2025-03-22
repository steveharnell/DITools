import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timedelta
import os
import json

class ProjectFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.output_directory = ""
        # Core fields
        self.job_var = tk.StringVar()
        self.client_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.preview_var = tk.StringVar(value="Preview will appear here")
        # Date Options
        self.var_date_today = tk.BooleanVar(value=True)
        self.var_date_custom = tk.BooleanVar(value=False)
        self.var_date_format_ymd = tk.BooleanVar(value=True)
        self.var_date_format_mdy = tk.BooleanVar(value=False)
        self.var_date_format_dmy = tk.BooleanVar(value=False)
        self.var_date_prefix = tk.BooleanVar(value=False)
        # Original Camera Negative Options
        self.var_orig_online = tk.BooleanVar(value=True)
        self.var_orig_ocn = tk.BooleanVar(value=False)
        self.var_orig_custom = tk.BooleanVar(value=False)
        # Transcode Options
        self.var_dnxdh = tk.BooleanVar(value=True)
        self.var_dnxhr = tk.BooleanVar(value=False)
        self.var_prores_proxy = tk.BooleanVar(value=False)
        self.var_prores_lt = tk.BooleanVar(value=False)
        self.var_custom = tk.BooleanVar(value=False)
        # Audio Options
        self.var_audio_default = tk.BooleanVar(value=True)
        self.var_audio_mos = tk.BooleanVar(value=False)
        self.var_audio_custom = tk.BooleanVar(value=False)
        # DIT Folder Options
        self.var_custom_dit = tk.BooleanVar(value=False)
        self.var_custom_dit2 = tk.BooleanVar(value=False)
        self.var_documents = tk.BooleanVar(value=True)
        self.var_dit_framing = tk.BooleanVar(value=True)
        self.var_dit_logs = tk.BooleanVar(value=True)
        self.var_dit_luts = tk.BooleanVar(value=True)
        self.var_dit_resolve = tk.BooleanVar(value=True)
        self.var_silverstack = tk.BooleanVar(value=False)
        self.var_dit_stills = tk.BooleanVar(value=True)
        # Multi Day Options
        self.var_single_day = tk.BooleanVar(value=True)
        self.var_multi_day = tk.BooleanVar(value=False)
        self.multi_day_choice = tk.IntVar(value=2)
        # Checkbox for DAY01_OF_DAY suffix
        self.var_day01_suffix = tk.BooleanVar(value=True)
        # Generate To All External Destinations
        self.var_generate_all_external = tk.BooleanVar(value=False)
        # Enable Numbered Subdirectories
        self.var_enable_numbering = tk.BooleanVar(value=False)
        self.build_ui()

    def build_ui(self):
        # Configure grid with three columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # Core project fields
        ttk.Label(self, text="Job Number:", style="DIT.TLabel").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.job_entry = ttk.Entry(self, textvariable=self.job_var)
        self.job_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.job_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        ttk.Label(self, text="Job Name/Client:", style="DIT.TLabel").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.client_entry = ttk.Entry(self, textvariable=self.client_var)
        self.client_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.client_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        ttk.Label(self, text="Production Co.:", style="DIT.TLabel").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.project_entry = ttk.Entry(self, textvariable=self.project_var)
        self.project_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.project_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        ttk.Label(self, text="Preview:", style="DIT.TLabel").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.preview_label = ttk.Label(self, textvariable=self.preview_var, style="DIT.TLabel")
        self.preview_label.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Buttons for selecting output and creating project
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        self.select_dir_button = ttk.Button(btn_frame, text="Select Output Directory", style="DIT.TButton",
                                            command=self.select_directory)
        self.select_dir_button.grid(row=0, column=0, padx=2)
        self.create_project_button = ttk.Button(btn_frame, text="Create Project", style="DIT.TButton",
                                                command=self.create_project)
        self.create_project_button.grid(row=0, column=1, padx=2)

        self.directory_label = ttk.Label(self, text="No directory selected", style="DIT.TLabel")
        self.directory_label.grid(row=5, column=0, columnspan=3, pady=5)

        # Date Options Frame
        date_frame = ttk.LabelFrame(self, text="Date Options", padding=5)
        date_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(date_frame, text="Today", variable=self.var_date_today,
                        command=lambda: self.select_date_option("today")).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(date_frame, text="Custom", variable=self.var_date_custom,
                        command=lambda: self.select_date_option("custom")).grid(row=0, column=1, sticky="w")
        self.date_custom_entry = ttk.Entry(date_frame, state='disabled')
        self.date_custom_entry.grid(row=0, column=2, padx=2, pady=2)
        self.date_custom_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        ttk.Checkbutton(date_frame, text="YYYYMMDD", variable=self.var_date_format_ymd,
                        command=lambda: self.select_date_format("ymd")).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(date_frame, text="MMDDYYYY", variable=self.var_date_format_mdy,
                        command=lambda: self.select_date_format("mdy")).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(date_frame, text="DDMMYYYY", variable=self.var_date_format_dmy,
                        command=lambda: self.select_date_format("dmy")).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(date_frame, text="Date as Prefix", variable=self.var_date_prefix,
                        command=self.update_preview).grid(row=0, column=3, sticky="w")

        # Multi Day Options Frame
        multi_day_frame = ttk.LabelFrame(self, text="Multi Day Options", padding=5)
        multi_day_frame.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(multi_day_frame, text="Single Day", variable=self.var_single_day,
                        command=self.select_single_day).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(multi_day_frame, text="Multi Day", variable=self.var_multi_day,
                        command=self.select_multi_day).grid(row=0, column=1, sticky="w")
        self.day01_suffix_checkbox = ttk.Checkbutton(
            multi_day_frame,
            text="DAY01_OF_DAY01",
            variable=self.var_day01_suffix,
            command=self.update_preview
        )
        self.day01_suffix_checkbox.grid(row=0, column=2, sticky="w", padx=2)
        rb_frame = ttk.Frame(multi_day_frame)
        rb_frame.grid(row=1, column=0, columnspan=3, pady=2)
        self.multi_day_radiobuttons = []
        for i, day in enumerate(range(2, 11)):
            rb = ttk.Radiobutton(rb_frame, text=f"{day} Days", variable=self.multi_day_choice, value=day,
                                 command=self.update_day01_suffix_text)
            rb.grid(row=0, column=i, padx=2)
            self.multi_day_radiobuttons.append(rb)
        self.set_multi_day_state("disabled")

        # Number Options Frame
        number_frame = ttk.LabelFrame(self, text="Number Options", padding=5)
        number_frame.grid(row=8, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(number_frame, text="Enable Numbered Subdirectories", variable=self.var_enable_numbering).grid(
            row=0, column=0, sticky="w")

        # Original Camera Negative Options Frame
        orig_frame = ttk.LabelFrame(self, text="Original Camera Negative Options", padding=5)
        orig_frame.grid(row=9, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(orig_frame, text="ORIGINAL_CAMERA_NEGATIVE_ONLINE", variable=self.var_orig_online,
                        command=lambda: self.select_orig("online")).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(orig_frame, text="OCN", variable=self.var_orig_ocn,
                        command=lambda: self.select_orig("ocn")).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(orig_frame, text="Custom", variable=self.var_orig_custom,
                        command=lambda: self.select_orig("custom")).grid(row=0, column=2, sticky="w")
        self.orig_custom_entry = ttk.Entry(orig_frame, state='disabled')
        self.orig_custom_entry.grid(row=0, column=3, padx=2, pady=2)
        self.orig_custom_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        # Transcode Options Frame
        transcode_frame = ttk.LabelFrame(self, text="Transcode Options", padding=5)
        transcode_frame.grid(row=10, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(transcode_frame, text="AVID_DNxHD_36_MXF_1080P_OFFLINE", variable=self.var_dnxdh).grid(
            row=0, column=0, sticky="w")
        ttk.Checkbutton(transcode_frame, text="AVID_DNxHR_LB_MXF_1080P_OFFLINE", variable=self.var_dnxhr).grid(
            row=1, column=0, sticky="w")
        ttk.Checkbutton(transcode_frame, text="PRORES_422_PROXY_1080P_OFFLINE", variable=self.var_prores_proxy).grid(
            row=2, column=0, sticky="w")
        ttk.Checkbutton(transcode_frame, text="PRORES_422_LT_1080P_OFFLINE", variable=self.var_prores_lt).grid(
            row=3, column=0, sticky="w")
        ttk.Checkbutton(transcode_frame, text="Custom", variable=self.var_custom,
                        command=self.toggle_custom_entry).grid(row=4, column=0, sticky="w")
        self.custom_entry = ttk.Entry(transcode_frame, state='disabled')
        self.custom_entry.grid(row=4, column=1, padx=2, pady=2)
        self.custom_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        # Audio Options Frame
        audio_frame = ttk.LabelFrame(self, text="Audio Options", padding=5)
        audio_frame.grid(row=11, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(audio_frame, text="AUDIO", variable=self.var_audio_default,
                        command=lambda: self.select_audio("audio")).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(audio_frame, text="MOS", variable=self.var_audio_mos,
                        command=lambda: self.select_audio("mos")).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(audio_frame, text="Custom", variable=self.var_audio_custom,
                        command=lambda: self.select_audio("custom")).grid(row=0, column=2, sticky="w")
        self.audio_custom_entry = ttk.Entry(audio_frame, state='disabled')
        self.audio_custom_entry.grid(row=0, column=3, padx=2, pady=2)
        self.audio_custom_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        # DIT Folder Options Frame
        dit_frame = ttk.LabelFrame(self, text="DIT Folder Options", padding=5)
        dit_frame.grid(row=12, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(dit_frame, text="Custom 1", variable=self.var_custom_dit,
                        command=self.toggle_custom_dit_entry).grid(row=0, column=0, sticky="w")
        self.custom_dit_entry = ttk.Entry(dit_frame, state='disabled')
        self.custom_dit_entry.grid(row=0, column=1, padx=2, pady=2)
        ttk.Checkbutton(dit_frame, text="Custom 2", variable=self.var_custom_dit2,
                        command=self.toggle_custom_dit2_entry).grid(row=0, column=2, sticky="w")
        self.custom_dit2_entry = ttk.Entry(dit_frame, state='disabled')
        self.custom_dit2_entry.grid(row=0, column=3, padx=2, pady=2)
        ttk.Checkbutton(dit_frame, text="DOCUMENTS", variable=self.var_documents).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(dit_frame, text="FRAMING_CHARTS", variable=self.var_dit_framing).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(dit_frame, text="LOGS", variable=self.var_dit_logs).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(dit_frame, text="LUTS", variable=self.var_dit_luts).grid(row=1, column=3, sticky="w")
        ttk.Checkbutton(dit_frame, text="RESOLVE_PROJECT", variable=self.var_dit_resolve).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(dit_frame, text="SILVERSTACK_LIBRARY", variable=self.var_silverstack).grid(row=2, column=1, sticky="w")
        ttk.Checkbutton(dit_frame, text="STILLS", variable=self.var_dit_stills).grid(row=2, column=2, sticky="w")

        # Settings Controls Frame (Import, Save, Template)
        settings_frame = ttk.LabelFrame(self, text="Settings Controls", padding=5)
        settings_frame.grid(row=13, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.import_settings_button = ttk.Button(settings_frame, text="Import Settings", style="DIT.TButton", command=self.import_settings)
        self.import_settings_button.grid(row=0, column=0, padx=2, pady=2)
        self.save_settings_button = ttk.Button(settings_frame, text="Save Settings", style="DIT.TButton", command=self.save_settings)
        self.save_settings_button.grid(row=0, column=1, padx=2, pady=2)
        self.show_template_button = ttk.Button(settings_frame, text="Show Template", style="DIT.TButton", command=self.show_template)
        self.show_template_button.grid(row=0, column=2, padx=2, pady=2)

    def set_multi_day_state(self, state):
        for rb in self.multi_day_radiobuttons:
            rb.config(state=state)

    def select_single_day(self):
        self.var_single_day.set(True)
        self.var_multi_day.set(False)
        self.set_multi_day_state("disabled")
        self.update_day01_suffix_text()
        self.update_preview()

    def select_multi_day(self):
        self.var_multi_day.set(True)
        self.var_single_day.set(False)
        self.set_multi_day_state("normal")
        self.update_day01_suffix_text()
        self.update_preview()

    def toggle_custom_entry(self):
        if self.var_custom.get():
            self.custom_entry.config(state='normal')
        else:
            self.custom_entry.delete(0, tk.END)
            self.custom_entry.config(state='disabled')
        self.update_preview()

    def toggle_custom_dit_entry(self):
        if self.var_custom_dit.get():
            self.custom_dit_entry.config(state='normal')
        else:
            self.custom_dit_entry.delete(0, tk.END)
            self.custom_dit_entry.config(state='disabled')
        self.update_preview()

    def toggle_custom_dit2_entry(self):
        if self.var_custom_dit2.get():
            self.custom_dit2_entry.config(state='normal')
        else:
            self.custom_dit2_entry.delete(0, tk.END)
            self.custom_dit2_entry.config(state='disabled')
        self.update_preview()

    def get_start_date(self):
        if self.var_date_today.get():
            return datetime.now()
        else:
            date_str = self.date_custom_entry.get().strip()
            fmt = "%Y%m%d" if self.var_date_format_ymd.get() else ("%m%d%Y" if self.var_date_format_mdy.get() else "%d%m%Y")
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                messagebox.showerror("Date Format Error", f"Custom date '{date_str}' does not match the selected format.")
                return datetime.now()

    def update_preview(self):
        job = self.job_var.get().strip()
        client = self.client_var.get().strip()
        project = self.project_var.get().strip()
        if self.var_multi_day.get():
            total_days = self.multi_day_choice.get()
            preview_lines = []
            start_date = self.get_start_date()
            for i in range(total_days):
                day_date = start_date + timedelta(days=i)
                date_str = (day_date.strftime("%Y%m%d") if self.var_date_format_ymd.get() 
                            else (day_date.strftime("%m%d%Y") if self.var_date_format_mdy.get() 
                                  else (day_date.strftime("%d%m%Y") if self.var_date_format_dmy.get() 
                                        else day_date.strftime("%Y%m%d"))))
                folder_name = (f"{date_str}_{job}_{client}_{project}" if self.var_date_prefix.get() 
                               else f"{job}_{client}_{project}_{date_str}")
                if self.var_day01_suffix.get():
                    folder_name += f"_DAY{(i+1):02d}_OF_DAY{total_days:02d}"
                preview_lines.append(folder_name)
            self.preview_var.set("\n".join(preview_lines))
        else:
            date_str = self.get_date_string()
            folder_name = (f"{date_str}_{job}_{client}_{project}" if self.var_date_prefix.get() 
                           else f"{job}_{client}_{project}_{date_str}")
            if self.var_day01_suffix.get():
                folder_name += "_DAY01_OF_DAY01"
            self.preview_var.set(folder_name)

    def get_date_string(self):
        if self.var_date_today.get():
            return datetime.now().strftime("%Y%m%d") if self.var_date_format_ymd.get() else (
                   datetime.now().strftime("%m%d%Y") if self.var_date_format_mdy.get() else (
                   datetime.now().strftime("%d%m%Y") if self.var_date_format_dmy.get() else datetime.now().strftime("%Y%m%d")))
        else:
            return self.date_custom_entry.get().strip()

    def select_date_option(self, option):
        if option == "today":
            self.var_date_today.set(True)
            self.var_date_custom.set(False)
        elif option == "custom":
            self.var_date_today.set(False)
            self.var_date_custom.set(True)
        self.toggle_date_custom_entry()
        self.update_preview()

    def toggle_date_custom_entry(self):
        if self.var_date_custom.get():
            self.date_custom_entry.config(state='normal')
        else:
            self.date_custom_entry.delete(0, tk.END)
            self.date_custom_entry.config(state='disabled')

    def select_date_format(self, option):
        if option == "ymd":
            self.var_date_format_ymd.set(True)
            self.var_date_format_mdy.set(False)
            self.var_date_format_dmy.set(False)
        elif option == "mdy":
            self.var_date_format_ymd.set(False)
            self.var_date_format_mdy.set(True)
            self.var_date_format_dmy.set(False)
        elif option == "dmy":
            self.var_date_format_ymd.set(False)
            self.var_date_format_mdy.set(False)
            self.var_date_format_dmy.set(True)
        self.update_preview()

    def select_orig(self, option):
        if option == "online":
            self.var_orig_online.set(True)
            self.var_orig_ocn.set(False)
            self.var_orig_custom.set(False)
        elif option == "ocn":
            self.var_orig_online.set(False)
            self.var_orig_ocn.set(True)
            self.var_orig_custom.set(False)
        elif option == "custom":
            self.var_orig_online.set(False)
            self.var_orig_ocn.set(False)
            self.var_orig_custom.set(True)
        self.toggle_custom_orig_entry()
        self.update_preview()

    def toggle_custom_orig_entry(self):
        if self.var_orig_custom.get():
            self.orig_custom_entry.config(state='normal')
        else:
            self.orig_custom_entry.delete(0, tk.END)
            self.orig_custom_entry.config(state='disabled')
        self.update_preview()

    def select_audio(self, option):
        if option == "audio":
            # If turning on, turn off others for exclusivity
            if self.var_audio_default.get():
                self.var_audio_mos.set(False)
                self.var_audio_custom.set(False)
        elif option == "mos":
            # If turning on, turn off others for exclusivity
            if self.var_audio_mos.get():
                self.var_audio_default.set(False)
                self.var_audio_custom.set(False)
        elif option == "custom":
            # If turning on, turn off others for exclusivity
            if self.var_audio_custom.get():
                self.var_audio_default.set(False)
                self.var_audio_mos.set(False)
        self.toggle_custom_audio_entry()
        self.update_preview()

    def toggle_custom_audio_entry(self):
        if self.var_audio_custom.get():
            self.audio_custom_entry.config(state='normal')
        else:
            self.audio_custom_entry.delete(0, tk.END)
            self.audio_custom_entry.config(state='disabled')
        self.update_preview()

    def update_day01_suffix_text(self):
        if self.var_multi_day.get():
            total_days = self.multi_day_choice.get()
            self.day01_suffix_checkbox.config(text=f"DAY{total_days:02d}_OF_DAYXX")
        else:
            self.day01_suffix_checkbox.config(text="DAY01_OF_DAY01")
        self.update_preview()

    def select_directory(self):
        selected_dir = filedialog.askdirectory(title="Select Output Directory")
        if selected_dir:
            self.output_directory = selected_dir
            self.directory_label.config(text=f"Output Directory: {self.output_directory}")

    def get_external_destinations(self, folder_name):
        destinations = []
        volumes_path = "/Volumes"
        forbidden = {"UNTITLED", "UNTITLED 2", "untitled", "untitled 2",
                     "NO NAME", "NONAME", "NO_NAME", "NEW VOLUME", "NEW_VOLUME",
                     "DISK", "SD", "SD Card", "SD_CARD", "SDCARD", "633", "888"}
        if os.path.exists(volumes_path):
            for vol in os.listdir(volumes_path):
                vol_path = os.path.join(volumes_path, vol)
                if os.path.isdir(vol_path) and vol not in forbidden:
                    destinations.append(os.path.join(vol_path, folder_name))
        return destinations

    def check_folder_conflicts(self, folder_paths):
        conflicts = [path for path in folder_paths if os.path.exists(path)]
        if self.var_generate_all_external.get():
            for folder in folder_paths:
                folder_name = os.path.basename(folder)
                ext_paths = self.get_external_destinations(folder_name)
                conflicts.extend([p for p in ext_paths if os.path.exists(p)])
        if conflicts:
            conflict_str = "\n".join(conflicts)
            result = messagebox.askyesno("Directory Conflict",
                                         f"The following directories already exist:\n{conflict_str}\n\n"
                                         f"Do you want to continue and overwrite them?")
            if not result:
                return True
        return False

    def create_structure_in_folder(self, base_path, date_str):
        if self.var_orig_online.get():
            orig_folder = f"ORIGINAL_CAMERA_NEGATIVE_ONLINE_{date_str}"
        elif self.var_orig_ocn.get():
            orig_folder = f"OCN_{date_str}"
        elif self.var_orig_custom.get():
            custom_orig = self.orig_custom_entry.get().strip()
            if not custom_orig:
                raise Exception("Custom Original Camera Negative option missing.")
            orig_folder = f"{custom_orig}_{date_str}"
        else:
            raise Exception("No Original Camera Negative option selected.")
        if self.var_enable_numbering.get():
            orig_folder = "01_" + orig_folder
        os.makedirs(os.path.join(base_path, orig_folder), exist_ok=True)

        # Create audio folder only if an audio option is selected
        if self.var_audio_default.get() or self.var_audio_mos.get() or self.var_audio_custom.get():
            if self.var_audio_default.get():
                audio_folder = f"AUDIO_{date_str}"
            elif self.var_audio_mos.get():
                audio_folder = f"MOS_{date_str}"
            elif self.var_audio_custom.get():
                custom_audio = self.audio_custom_entry.get().strip()
                if not custom_audio:
                    raise Exception("Custom Audio option missing.")
                audio_folder = f"{custom_audio}_{date_str}"

            if self.var_enable_numbering.get():
                audio_folder = "03_" + audio_folder

            os.makedirs(os.path.join(base_path, audio_folder), exist_ok=True)

        transcode_dirs = []
        if self.var_dnxdh.get():
            transcode_dirs.append(f"AVID_DNxHD_36_MXF_1080P_OFFLINE_{date_str}")
        if self.var_dnxhr.get():
            transcode_dirs.append(f"AVID_DNxHR_LB_MXF_1080P_OFFLINE_{date_str}")
        if self.var_prores_proxy.get():
            transcode_dirs.append(f"PRORES_422_PROXY_1080P_OFFLINE_{date_str}")
        if self.var_prores_lt.get():
            transcode_dirs.append(f"PRORES_422_LT_1080P_OFFLINE_{date_str}")
        if self.var_custom.get():
            custom_text = self.custom_entry.get().strip()
            if custom_text:
                transcode_dirs.append(f"{custom_text}_{date_str}")
        if self.var_enable_numbering.get():
            if len(transcode_dirs) == 1:
                transcode_dirs[0] = "02_" + transcode_dirs[0]
            elif len(transcode_dirs) > 1:
                for i in range(len(transcode_dirs)):
                    transcode_dirs[i] = f"02_{i + 1}_" + transcode_dirs[i]
        for folder in transcode_dirs:
            os.makedirs(os.path.join(base_path, folder), exist_ok=True)

        dit_folder = f"DIT_{date_str}"
        if self.var_enable_numbering.get():
            dit_folder = "04_" + dit_folder
        dit_path = os.path.join(base_path, dit_folder)
        os.makedirs(dit_path, exist_ok=True)
        if self.var_custom_dit.get():
            subfolder = self.custom_dit_entry.get().strip()
            os.makedirs(os.path.join(dit_path, subfolder), exist_ok=True)
        if self.var_custom_dit2.get():
            subfolder = self.custom_dit2_entry.get().strip()
            os.makedirs(os.path.join(dit_path, subfolder), exist_ok=True)
        if self.var_documents.get():
            os.makedirs(os.path.join(dit_path, "DOCUMENTS"), exist_ok=True)
        if self.var_dit_framing.get():
            os.makedirs(os.path.join(dit_path, "FRAMING_CHARTS"), exist_ok=True)
        if self.var_dit_logs.get():
            os.makedirs(os.path.join(dit_path, "LOGS"), exist_ok=True)
        if self.var_dit_luts.get():
            os.makedirs(os.path.join(dit_path, "LUTS"), exist_ok=True)
        if self.var_dit_resolve.get():
            os.makedirs(os.path.join(dit_path, "RESOLVE_PROJECT"), exist_ok=True)
        if self.var_silverstack.get():
            os.makedirs(os.path.join(dit_path, "SILVERSTACK_LIBRARY"), exist_ok=True)
        if self.var_dit_stills.get():
            os.makedirs(os.path.join(dit_path, "STILLS"), exist_ok=True)

    def create_project(self):
        job = self.job_var.get().strip()
        client = self.client_var.get().strip()
        project = self.project_var.get().strip()
        if not job or not client or not project:
            messagebox.showwarning("Missing Information", "Please fill in all fields.")
            return
        if not self.output_directory:
            messagebox.showwarning("No Output Directory", "Please select an output directory.")
            return

        if self.var_multi_day.get():
            total_days = self.multi_day_choice.get()
            start_date = self.get_start_date()
            folder_paths = []
            for i in range(total_days):
                day_date = start_date + timedelta(days=i)
                date_str = (day_date.strftime("%Y%m%d") if self.var_date_format_ymd.get() 
                            else (day_date.strftime("%m%d%Y") if self.var_date_format_mdy.get() 
                                  else (day_date.strftime("%d%m%Y") if self.var_date_format_dmy.get() 
                                        else day_date.strftime("%Y%m%d"))))
                main_folder_name = (f"{date_str}_{job}_{client}_{project}" 
                                    if self.var_date_prefix.get() 
                                    else f"{job}_{client}_{project}_{date_str}")
                if self.var_day01_suffix.get():
                    main_folder_name += f"_DAY{(i+1):02d}_OF_DAY{total_days:02d}"
                folder_paths.append(os.path.join(self.output_directory, main_folder_name))
            if self.check_folder_conflicts(folder_paths):
                return
            for i in range(total_days):
                day_date = start_date + timedelta(days=i)
                date_str = (day_date.strftime("%Y%m%d") if self.var_date_format_ymd.get() 
                            else (day_date.strftime("%m%d%Y") if self.var_date_format_mdy.get() 
                                  else (day_date.strftime("%d%m%Y") if self.var_date_format_dmy.get() 
                                        else day_date.strftime("%Y%m%d"))))
                main_folder_name = (f"{date_str}_{job}_{client}_{project}" 
                                    if self.var_date_prefix.get() 
                                    else f"{job}_{client}_{project}_{date_str}")
                if self.var_day01_suffix.get():
                    main_folder_name += f"_DAY{(i+1):02d}_OF_DAY{total_days:02d}"
                main_folder_path = os.path.join(self.output_directory, main_folder_name)
                os.makedirs(main_folder_path, exist_ok=True)
                self.create_structure_in_folder(main_folder_path, date_str)
                if self.var_generate_all_external.get():
                    forbidden = {"UNTITLED", "UNTITLED 2", "untitled", "untitled 2",
                                 "NO NAME", "NONAME", "NO_NAME", "NEW VOLUME", "NEW_VOLUME",
                                 "DISK", "SD", "SD Card", "SD_CARD", "SDCARD", "633", "888"}
                    volumes_path = "/Volumes"
                    if os.path.exists(volumes_path):
                        for vol in os.listdir(volumes_path):
                            vol_path = os.path.join(volumes_path, vol)
                            if os.path.isdir(vol_path) and vol not in forbidden:
                                dest = os.path.join(vol_path, main_folder_name)
                                try:
                                    os.makedirs(dest, exist_ok=True)
                                    self.create_structure_in_folder(dest, date_str)
                                except OSError as err:
                                    if err.errno in (13, 30):
                                        continue
                                    else:
                                        raise
            msg = f"Project directories created for {total_days} day(s) in {self.output_directory}"
            messagebox.showinfo("Success", msg)
        else:
            date_str = self.get_date_string()
            main_folder_name = (f"{date_str}_{job}_{client}_{project}" 
                                if self.var_date_prefix.get() 
                                else f"{job}_{client}_{project}_{date_str}")
            if self.var_day01_suffix.get():
                main_folder_name += "_DAY01_OF_DAY01"
            folder_paths = [os.path.join(self.output_directory, main_folder_name)]
            if self.check_folder_conflicts(folder_paths):
                return
            folder_path = folder_paths[0]
            os.makedirs(folder_path, exist_ok=True)
            self.create_structure_in_folder(folder_path, date_str)
            if self.var_generate_all_external.get():
                forbidden = {"UNTITLED", "UNTITLED 2", "untitled", "untitled 2",
                             "NO NAME", "NONAME", "NO_NAME", "NEW VOLUME", "NEW_VOLUME",
                             "DISK", "SD", "SD Card", "SD_CARD", "SDCARD", "633", "888"}
                volumes_path = "/Volumes"
                if os.path.exists(volumes_path):
                    for vol in os.listdir(volumes_path):
                        vol_path = os.path.join(volumes_path, vol)
                        if os.path.isdir(vol_path) and vol not in forbidden:
                            dest = os.path.join(vol_path, main_folder_name)
                            try:
                                os.makedirs(dest, exist_ok=True)
                                self.create_structure_in_folder(dest, date_str)
                            except OSError as err:
                                if err.errno in (13, 30):
                                    continue
                                else:
                                    raise
            messagebox.showinfo("Success", f"Project directories created at:\n{folder_path}")

    def validate_settings(self, settings):
        errors = []
        if not settings.get("job"):
            errors.append("Job field is required.")
        if not settings.get("client"):
            errors.append("Client field is required.")
        if not settings.get("project"):
            errors.append("Project field is required.")
        if settings.get("date_custom", False):
            custom_date = settings.get("custom_date", "")
            date_format = settings.get("date_format", "ymd")
            fmt = "%Y%m%d" if date_format == "ymd" else ("%m%d%Y" if date_format == "mdy" else "%d%m%Y")
            try:
                datetime.strptime(custom_date, fmt)
            except Exception:
                errors.append(f"Custom date '{custom_date}' is invalid for format '{date_format}'.")
        if settings.get("orig_option", "online") == "custom" and not settings.get("custom_orig", ""):
            errors.append("Custom Original Camera Negative option selected but 'custom_orig' is missing.")
        if settings.get("multi_day", False):
            mdc = settings.get("multi_day_choice", None)
            if mdc is None:
                errors.append("Multi day is enabled but 'multi_day_choice' is missing.")
            else:
                try:
                    mdc_int = int(mdc)
                    if mdc_int < 1:
                        errors.append("Multi day choice must be at least 1.")
                except Exception:
                    errors.append("Multi day choice must be an integer.")
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

        # Check if this is a project settings file
        if settings.get("module") != "project":
            messagebox.showerror("Settings Error", "The selected file is not a valid project settings file.")
            return

        errors = self.validate_settings(settings)
        if errors:
            messagebox.showerror("Settings Error", "The following errors were found:\n" + "\n".join(errors))
            return

        # Populate core fields
        self.job_var.set(settings.get("job", ""))
        self.client_var.set(settings.get("client", ""))
        self.project_var.set(settings.get("project", ""))

        # Date Options
        if settings.get("date_custom", False):
            self.var_date_custom.set(True)
            self.var_date_today.set(False)
            self.date_custom_entry.config(state="normal")
            self.date_custom_entry.delete(0, tk.END)
            self.date_custom_entry.insert(0, settings.get("custom_date", ""))
        else:
            self.var_date_custom.set(False)
            self.var_date_today.set(True)
            self.date_custom_entry.delete(0, tk.END)
            self.date_custom_entry.config(state="disabled")
        date_format = settings.get("date_format", "ymd")
        self.var_date_format_ymd.set(date_format == "ymd")
        self.var_date_format_mdy.set(date_format == "mdy")
        self.var_date_format_dmy.set(date_format == "dmy")
        self.var_date_prefix.set(settings.get("date_prefix", False))

        # Original Camera Negative Options
        orig_option = settings.get("orig_option", "online")
        if orig_option == "online":
            self.select_orig("online")
        elif orig_option == "ocn":
            self.select_orig("ocn")
        elif orig_option == "custom":
            self.select_orig("custom")
            self.orig_custom_entry.config(state="normal")
            self.orig_custom_entry.delete(0, tk.END)
            self.orig_custom_entry.insert(0, settings.get("custom_orig", ""))

        # Transcode Options
        self.var_dnxdh.set(settings.get("dnxdh", True))
        self.var_dnxhr.set(settings.get("dnxhr", False))
        self.var_prores_proxy.set(settings.get("prores_proxy", False))
        self.var_prores_lt.set(settings.get("prores_lt", False))
        self.var_custom.set(settings.get("custom_transcode", False))
        if self.var_custom.get():
            self.custom_entry.config(state="normal")
            self.custom_entry.delete(0, tk.END)
            self.custom_entry.insert(0, settings.get("custom_transcode_value", ""))
        else:
            self.custom_entry.delete(0, tk.END)
            self.custom_entry.config(state="disabled")

        # Audio Options
        audio_option = settings.get("audio_option", "audio")
        if audio_option == "audio":
            self.var_audio_default.set(True)
            self.var_audio_mos.set(False)
            self.var_audio_custom.set(False)
        elif audio_option == "mos":
            self.var_audio_default.set(False)
            self.var_audio_mos.set(True)
            self.var_audio_custom.set(False)
        elif audio_option == "custom":
            self.var_audio_default.set(False)
            self.var_audio_mos.set(False)
            self.var_audio_custom.set(True)
        if self.var_audio_custom.get():
            self.audio_custom_entry.config(state="normal")
            self.audio_custom_entry.delete(0, tk.END)
            self.audio_custom_entry.insert(0, settings.get("custom_audio", ""))
        else:
            self.audio_custom_entry.delete(0, tk.END)
            self.audio_custom_entry.config(state="disabled")

        # Multi Day Options
        if settings.get("multi_day", False):
            self.var_multi_day.set(True)
            self.var_single_day.set(False)
            self.set_multi_day_state("normal")
            self.multi_day_choice.set(int(settings.get("multi_day_choice", 2)))
        else:
            self.var_multi_day.set(False)
            self.var_single_day.set(True)
            self.set_multi_day_state("disabled")
        self.var_day01_suffix.set(settings.get("day01_suffix", True))
        self.var_generate_all_external.set(settings.get("generate_all_external", False))
        self.var_enable_numbering.set(settings.get("enable_numbering", False))

        # DIT Folder Options
        self.var_custom_dit.set(settings.get("custom_dit", False))
        if self.var_custom_dit.get():
            self.custom_dit_entry.config(state="normal")
            self.custom_dit_entry.delete(0, tk.END)
            self.custom_dit_entry.insert(0, settings.get("custom_dit_value", ""))
        else:
            self.custom_dit_entry.delete(0, tk.END)
            self.custom_dit_entry.config(state="disabled")
        self.var_custom_dit2.set(settings.get("custom_dit2", False))
        if self.var_custom_dit2.get():
            self.custom_dit2_entry.config(state="normal")
            self.custom_dit2_entry.delete(0, tk.END)
            self.custom_dit2_entry.insert(0, settings.get("custom_dit2_value", ""))
        else:
            self.custom_dit2_entry.delete(0, tk.END)
            self.custom_dit2_entry.config(state="disabled")
        self.var_documents.set(settings.get("documents", True))
        self.var_dit_framing.set(settings.get("dit_framing", True))
        self.var_dit_logs.set(settings.get("dit_logs", True))
        self.var_dit_luts.set(settings.get("dit_luts", True))
        self.var_dit_resolve.set(settings.get("dit_resolve", True))
        self.var_silverstack.set(settings.get("silverstack", False))
        self.var_dit_stills.set(settings.get("dit_stills", True))

        self.update_preview()
        messagebox.showinfo("Import Settings", "Settings imported successfully.")

    def save_settings(self):
        settings = {
            "module": "project",  # Identifier for project settings
            "job": self.job_var.get().strip(),
            "client": self.client_var.get().strip(),
            "project": self.project_var.get().strip(),
            "date_custom": self.var_date_custom.get(),
            "custom_date": self.date_custom_entry.get().strip() if self.var_date_custom.get() else "",
            "date_format": "ymd" if self.var_date_format_ymd.get() else ("mdy" if self.var_date_format_mdy.get() else "dmy"),
            "date_prefix": self.var_date_prefix.get(),
            "orig_option": "custom" if self.var_orig_custom.get() else ("ocn" if self.var_orig_ocn.get() else "online"),
            "custom_orig": self.orig_custom_entry.get().strip() if self.var_orig_custom.get() else "",
            "dnxdh": self.var_dnxdh.get(),
            "dnxhr": self.var_dnxhr.get(),
            "prores_proxy": self.var_prores_proxy.get(),
            "prores_lt": self.var_prores_lt.get(),
            "custom_transcode": self.var_custom.get(),
            "custom_transcode_value": self.custom_entry.get().strip() if self.var_custom.get() else "",
            "audio_option": "custom" if self.var_audio_custom.get() else ("mos" if self.var_audio_mos.get() else "audio"),
            "custom_audio": self.audio_custom_entry.get().strip() if self.var_audio_custom.get() else "",
            "multi_day": self.var_multi_day.get(),
            "multi_day_choice": self.multi_day_choice.get() if self.var_multi_day.get() else 1,
            "day01_suffix": self.var_day01_suffix.get(),
            "generate_all_external": self.var_generate_all_external.get(),
            "enable_numbering": self.var_enable_numbering.get(),
            "custom_dit": self.var_custom_dit.get(),
            "custom_dit_value": self.custom_dit_entry.get().strip() if self.var_custom_dit.get() else "",
            "custom_dit2": self.var_custom_dit2.get(),
            "custom_dit2_value": self.custom_dit2_entry.get().strip() if self.var_custom_dit2.get() else "",
            "documents": self.var_documents.get(),
            "dit_framing": self.var_dit_framing.get(),
            "dit_logs": self.var_dit_logs.get(),
            "dit_luts": self.var_dit_luts.get(),
            "dit_resolve": self.var_dit_resolve.get(),
            "silverstack": self.var_silverstack.get(),
            "dit_stills": self.var_dit_stills.get()
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
            
        # Ensure the filename includes "_project" suffix
        if filename.endswith(".json"):
            base = filename[:-5]
            if not base.endswith("_project"):
                filename = base + "_project.json"
        else:
            if not filename.endswith("_project"):
                filename = filename + "_project.json"
            else:
                filename = filename + ".json"
        
        try:
            with open(filename, "w") as f:
                json.dump(settings, f, indent=4)
            messagebox.showinfo("Save Settings", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings file: {e}")

    def show_template(self):
        sample = {
            "job": "1234",
            "client": "Acme Corp",
            "project": "ProductionCo",
            "date_custom": True,
            "custom_date": "20250312",
            "date_format": "ymd",
            "date_prefix": False,
            "orig_option": "custom",
            "custom_orig": "MyCustomOrig",
            "dnxdh": True,
            "dnxhr": False,
            "prores_proxy": False,
            "prores_lt": False,
            "custom_transcode": False,
            "custom_transcode_value": "",
            "audio_option": "audio",
            "custom_audio": "",
            "multi_day": True,
            "multi_day_choice": 3,
            "day01_suffix": True,
            "generate_all_external": False,
            "enable_numbering": False,
            "custom_dit": False,
            "custom_dit_value": "",
            "custom_dit2": False,
            "custom_dit2_value": "",
            "documents": True,
            "dit_framing": True,
            "dit_logs": True,
            "dit_luts": True,
            "dit_resolve": True,
            "silverstack": False,
            "dit_stills": True
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

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Project")
    project_frame = ProjectFrame(root)
    project_frame.pack(fill="both", expand=True)
    root.mainloop()