# +++++++++++++++
# autosort_app.py
# +++++++++++++++
import customtkinter as ctk
import threading
import time
import csv
from tkinter import filedialog, ttk
from pathlib import Path
import content_engine
import organizer_core

# standardizing the UI palette to give it a dark theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLOR_SIDEBAR = "#1A1A1A"
COLOR_MAIN_BG = "#242424"
COLOR_ACCENT = "#C5A028"
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GREY = "#A0A0A0"
COLOR_CARD_BG = "#2B2B2B"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        tw.attributes("-topmost", True)
        
        label = ctk.CTkLabel(tw, text=self.text, justify="left", fg_color="#2B2B2B", text_color="white", corner_radius=6, padx=10, pady=5)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class AutoSortApp(ctk.CTk):
    def __init__(self):
        # initializing the window
        super().__init__()

        self.title("AutoSort")
        self.geometry("1150x780")
        self.minsize(1150, 780)       
        self.resizable(False, False)  
    
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # map for the file paths
        self.file_map = {} 
        self.selected_folder = None

        # loading the npl model in a daemon thread to prevent gui from freezing on start up
        threading.Thread(target=content_engine.init_nlp_model, daemon=True).start()
        
        # constructing the sadbar ui
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="AutoSort", font=("Helvetica", 28, "bold"), text_color=COLOR_ACCENT).grid(row=0, column=0, padx=20, pady=(30, 5), sticky="w")
        self.lbl_system = ctk.CTkLabel(self.sidebar, text="Loading NLP Model...", font=("Helvetica", 12), text_color=COLOR_TEXT_GREY)
        self.lbl_system.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        self.btn_select = ctk.CTkButton(self.sidebar, text="📂 Select Folder", command=self.select_folder, fg_color=COLOR_MAIN_BG, border_width=1, border_color="gray30", height=40)
        self.btn_select.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # tabs to separate simple and smart mode
        self.tab_view = ctk.CTkTabview(self.sidebar, width=250, height=400, fg_color=COLOR_SIDEBAR, segmented_button_fg_color=COLOR_MAIN_BG, segmented_button_selected_color=COLOR_ACCENT, segmented_button_selected_hover_color=COLOR_ACCENT, segmented_button_unselected_color=COLOR_MAIN_BG)
        self.tab_view.grid(row=3, column=0, padx=15, pady=20, sticky="nsew")
        
        self.tab_basic = self.tab_view.add("BASIC MODE")
        self.tab_smart = self.tab_view.add("SMART MODE")

        ctk.CTkLabel(self.tab_basic, text="EXTENSION FILTERS:", font=("Helvetica", 11, "bold"), text_color="gray").pack(pady=(10, 10), anchor="w")
        
        self.chk_img = ctk.CTkCheckBox(self.tab_basic, text="Images", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_doc = ctk.CTkCheckBox(self.tab_basic, text="Documents", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_aud = ctk.CTkCheckBox(self.tab_basic, text="Audio", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_vid = ctk.CTkCheckBox(self.tab_basic, text="Video", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_exe = ctk.CTkCheckBox(self.tab_basic, text="Executables", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_arc = ctk.CTkCheckBox(self.tab_basic, text="Archives (Zip)", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        self.chk_cod = ctk.CTkCheckBox(self.tab_basic, text="Code Files", hover_color=COLOR_ACCENT, fg_color=COLOR_ACCENT)
        
        checkboxes = [self.chk_img, self.chk_doc, self.chk_aud, self.chk_vid, self.chk_exe, self.chk_arc, self.chk_cod]
        for chk in checkboxes:
            chk.pack(pady=5, anchor="w")
            chk.select() 

        # semantic tags ui
        tag_lbl_frame = ctk.CTkFrame(self.tab_smart, fg_color="transparent")
        tag_lbl_frame.pack(pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(tag_lbl_frame, text="SEMANTIC TAGS:", font=("Helvetica", 11, "bold"), text_color="gray").pack(side="left")
        
        tag_info = ctk.CTkLabel(tag_lbl_frame, text=" ⓘ ", font=("Helvetica", 14), text_color=COLOR_ACCENT, cursor="hand2")
        tag_info.pack(side="left", padx=(5, 0))
        
        ToolTip(tag_info, "Type comma-separated tags.\n\nSupported Aliases bypass AI (faster):\nvideos, movies, apps, zips, pics, photos,\npictures, music, docs, scripts.\n\nUnmatched tags trigger AI document scanning.")

        self.entry_tags = ctk.CTkEntry(self.tab_smart, placeholder_text="e.g. Invoice, Vacation", height=35)
        self.entry_tags.pack(pady=(0, 15), fill="x")
        
        # threshold ui
        thresh_lbl_frame = ctk.CTkFrame(self.tab_smart, fg_color="transparent")
        thresh_lbl_frame.pack(pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(thresh_lbl_frame, text="AI CONFIDENCE THRESHOLD:", font=("Helvetica", 11, "bold"), text_color="gray").pack(side="left")
        
        thresh_info = ctk.CTkLabel(thresh_lbl_frame, text=" ⓘ ", font=("Helvetica", 14), text_color=COLOR_ACCENT, cursor="hand2")
        thresh_info.pack(side="left", padx=(5, 0))
        
        ToolTip(thresh_info, "Minimum certainty required for AI categorization.\n\nHigh (70+%): Strict sorting, more files left as 'Others'.\nLow (25-%): Broad sorting, higher risk of misclassification.")

        self.slider_val = ctk.StringVar(value="30%")
        self.slider_label = ctk.CTkLabel(self.tab_smart, textvariable=self.slider_val, font=("Helvetica", 11), text_color="white")
        self.slider_label.pack(anchor="e", padx=5)
        
        self.confidence_slider = ctk.CTkSlider(self.tab_smart, from_=0.1, to=0.9, command=self.update_slider, button_color=COLOR_ACCENT, progress_color=COLOR_ACCENT)
        self.confidence_slider.set(0.3)
        self.confidence_slider.pack(fill="x", pady=5)
        
        self.btn_start = ctk.CTkButton(self.sidebar, text="START ORGANIZE", command=self.start_thread, fg_color=COLOR_ACCENT, text_color="black", height=45, font=("Helvetica", 14, "bold"), state="disabled")
        self.btn_start.grid(row=5, column=0, padx=20, pady=30, sticky="ew")

        self.main_area = ctk.CTkFrame(self, fg_color=COLOR_MAIN_BG, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.tree_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.tree_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        # treeview doesn't support CustomTkinter styling natively, so I manually override the ttk theme.
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLOR_CARD_BG, foreground=COLOR_TEXT_WHITE, fieldbackground=COLOR_CARD_BG, bordercolor=COLOR_MAIN_BG, rowheight=30)
        style.configure("Treeview.Heading", background=COLOR_SIDEBAR, foreground=COLOR_TEXT_GREY, borderwidth=0)
        style.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "black")])

        self.tree = ttk.Treeview(self.tree_frame, columns=("type", "dest", "status"), show="tree headings")
        self.tree.heading("#0", text="File Name", anchor="w")
        self.tree.heading("type", text="Type", anchor="center")
        self.tree.heading("dest", text="Destination", anchor="center")
        self.tree.heading("status", text="Status", anchor="center")
        self.tree.column("#0", width=350)
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("dest", width=150, anchor="center")
        self.tree.column("status", width=200, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # prevents users from messing up the table layout by dragging column headers
        def handle_column_click(event):
            if self.tree.identify_region(event.x, event.y) == "separator":
                return "break"
        self.tree.bind('<Button-1>', handle_column_click)
        
        self.scrollbar = ctk.CTkScrollbar(self.tree_frame, command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.progress_bar = ctk.CTkProgressBar(self.main_area, progress_color=COLOR_ACCENT, height=10)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=(0,20), sticky="ew")
        
        self.check_nlp_status()

    def update_slider(self, value):
        self.slider_val.set(f"{int(value * 100)}%")

    # polling ensures we don't let the user start sorting before the AI engine is actually loaded
    def check_nlp_status(self):
        if content_engine.classifier is not None:
            self.lbl_system.configure(text="AI Model Loaded")
        else:
            self.after(1000, self.check_nlp_status)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_folder = path
            self.btn_start.configure(state="normal")
            threading.Thread(target=self.preview_files, args=(path,), daemon=True).start()

    # gives the user instant feedback by listing files before the sorting actually begins
    def preview_files(self, path):
        self.tree.delete(*self.tree.get_children())
        self.file_map.clear()
        root = Path(path)
        try:
            for file_path in root.rglob("*"):
                # we skip hidden system files to avoid breaking OS-specific directory metadata
                if file_path.is_file() and not file_path.name.startswith('.'):
                    item_id = self.tree.insert("", "end", text=file_path.name, values=(file_path.suffix, "-", "Pending"))
                    self.file_map[str(file_path)] = item_id
        except: pass

    def start_thread(self):
        self.btn_start.configure(state="disabled", text="PROCESSING...")
        self.progress_bar.set(0)
        # processing must be threaded so the gui remains responsive and the progress bar updates in real time
        threading.Thread(target=self.run_logic, daemon=True).start()

    def update_status(self, file_path, dest_folder, status_text):
        item_id = self.file_map.get(str(file_path))
        if item_id:
            # tkinter isnt thread-safe, so i schedule ui updates to run on the main thread
            self.after(0, lambda: self._apply_update(item_id, dest_folder, status_text))
    
    def _apply_update(self, item_id, dest_folder, status_text):
        try:
            self.tree.set(item_id, "dest", dest_folder)
            self.tree.set(item_id, "status", status_text)
            self.tree.see(item_id)
        except: pass

    def run_logic(self):
        root = Path(self.selected_folder)
        start_time = time.time()
        report_data = []
        
        current_tab = self.tab_view.get() 
        is_smart_mode = (current_tab == "SMART MODE")
        threshold = self.confidence_slider.get()

        # hardcoded definitions for when the AI isn't used or doesn't find a match.
        ext_defs = {
            "Images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
            "Documents": ['.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.csv', '.rtf', '.epub', '.odt'],
            "Audio": ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            "Video": ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
            "Executables": ['.exe', '.msi', '.bat', '.cmd', '.iso', '.sh', '.apk'],
            "Archives": ['.zip', '.rar', '.7z', '.tar', '.gz', '.pkg', '.deb'],
            "Code": ['.py', '.js', '.html', '.css', '.cpp', '.java', '.json', '.xml']
        }

        active_ext_rules = {} 
        active_content_tags = [] 

        # map user checkbox selections to folder names.
        if not is_smart_mode:
            if self.chk_img.get(): active_ext_rules.update({ext: "Images" for ext in ext_defs["Images"]})
            if self.chk_doc.get(): active_ext_rules.update({ext: "Documents" for ext in ext_defs["Documents"]})
            if self.chk_aud.get(): active_ext_rules.update({ext: "Audio" for ext in ext_defs["Audio"]})
            if self.chk_vid.get(): active_ext_rules.update({ext: "Video" for ext in ext_defs["Video"]})
            if self.chk_exe.get(): active_ext_rules.update({ext: "Executables" for ext in ext_defs["Executables"]})
            if self.chk_arc.get(): active_ext_rules.update({ext: "Archives" for ext in ext_defs["Archives"]})
            if self.chk_cod.get(): active_ext_rules.update({ext: "Code" for ext in ext_defs["Code"]})
        
        else:
            raw_tags = self.entry_tags.get()
            user_tags = [tag.strip() for tag in raw_tags.split(',')] if raw_tags.strip() else []

            # aliases allow users to type "pics" and have the app understand they mean the "Images" extension group.
            tag_aliases = {
                "videos": "Video", "movies": "Video", "film": "Video",
                "apps": "Executables", "app": "Executables", "applications": "Executables", "programs": "Executables",
                "zips": "Archives", "zip": "Archives", "compressed": "Archives",
                "pics": "Images", "photos": "Images", "pictures": "Images",
                "music": "Audio", "songs": "Audio", "sounds": "Audio",
                "docs": "Documents", "papers": "Documents",
                "scripts": "Code", "coding": "Code"
            }

            for tag in user_tags:
                tag_lower = tag.lower()
                matched_key = None

                found_key = next((k for k in ext_defs if k.lower() == tag_lower), None)
                if found_key:
                    matched_key = found_key

                if not matched_key and tag_lower in tag_aliases:
                    matched_key = tag_aliases[tag_lower]

                # if the tag matches a known category, we use extension rules
                # else pass it to the NLP engine
                if matched_key:
                    folder_name = tag.capitalize() 
                    for ext in ext_defs[matched_key]:
                        active_ext_rules[ext] = folder_name
                else:
                    active_content_tags.append(tag)

        files = [f for f in root.rglob('*') if f.is_file()]
        total = len(files)
        
        for i, file_path in enumerate(files):
            self.progress_bar.set((i+1)/total)
            if file_path.name.startswith('.'): continue
            
            target_category = "Others"
            ext = file_path.suffix.lower()
            sorted_flag = False
            status_msg = ""

            # only attempt NLP on files that likely contain readable text or OCR-able visual data
            if is_smart_mode and active_content_tags and ext in ['.png', '.jpg', '.jpeg', '.pdf', '.txt', '.docx']:
                self.update_status(file_path, "Scanning...", "NLP Reading")
                text = ""
                try:
                    if ext == '.pdf': text = content_engine.extract_text_from_pdf(file_path)
                    elif ext == '.docx': text = content_engine.extract_text_from_docx(file_path)
                    elif ext == '.txt': 
                        try: text = file_path.read_text(errors='ignore')
                        except: pass
                    else: text = content_engine.extract_text_from_image(file_path)
                    
                    match = content_engine.analyze_content_smart(text, active_content_tags, threshold)
                    if match:
                        target_category = match
                        sorted_flag = True
                        status_msg = f"NLP Match ({match})"
                except: pass

            # extension based sorting is our backup if NLP fails or isn't being used.
            if not sorted_flag:
                if ext in active_ext_rules:
                    target_category = active_ext_rules[ext]
                    sorted_flag = True
                    status_msg = f"Ext Match ({ext})"
                else:
                    status_msg = "Fallback (Others)"

            dest = root / target_category
            # no point in moving a file if it's already in the right place
            if file_path.parent == dest:
                self.update_status(file_path, target_category, "No Change")
                report_data.append([file_path.name, target_category, "No Change", "Basic"])
                continue

            if organizer_core.move_file(file_path, dest):
                self.update_status(file_path, target_category, status_msg)
                sort_method = "NLP" if "NLP" in status_msg else "Extension"
                report_data.append([file_path.name, target_category, "Moved", sort_method])
            else:
                self.update_status(file_path, "-", "Error")
                report_data.append([file_path.name, "FAILED", "Error", "None"])

        # leave the filesystem tidy by deleting folders that no longer contain files
        organizer_core.clean_empty_folders(root)
        self.after(0, lambda: self.btn_start.configure(state="normal", text="ORGANIZE FILES"))

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # benchmarking data is saved to CSV so users can verify the efficiency and accuracy of the run
        mode_name = "SMART" if is_smart_mode else "BASIC"
        report_filename = f"benchmark_report_{mode_name}_{int(start_time)}.csv"
        
        with open(report_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Execution Time (Seconds):", f"{elapsed_time:.3f}"])
            writer.writerow(["Total Files Processed:", total])
            writer.writerow(["Threshold Set:", f"{threshold:.2f}" if is_smart_mode else "N/A"])
            writer.writerow([])
            writer.writerow(["File Name", "Destination Folder", "Status", "Sorting Method"])
            writer.writerows(report_data)
            
        print(f"Benchmark complete. Report saved as {report_filename} in {elapsed_time:.3f} seconds.")

if __name__ == "__main__":
    app = AutoSortApp()
    app.mainloop()