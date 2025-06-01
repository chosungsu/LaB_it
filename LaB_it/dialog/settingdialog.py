import customtkinter as ctk
from setting import *
from CTkMenuBar import *
import os
import json
from tkinter import messagebox, ttk, filedialog
import tkinter as tk

class SetupDialog(ctk.CTkToplevel):
    def __init__(self, master, task_name, on_setup_done, source_type, on_back_to_main=None):
        super().__init__(master)
        self.title("LaB_it-Setup")
        self.geometry("800x500")
        self.resizable(False, False)
        self.task_name = task_name
        self.on_setup_done = on_setup_done
        self.on_back_to_main = on_back_to_main
        self.folder_id = ""
        self.local_folder_path = ""
        self.labels = []
        self.label_dict = {}
        self.label_txt_path = None
        self.TASKS_DIR = TASKS_DIR
        self.ANNOTATIONS_DIR = ANNOTATIONS_DIR
        self.task_path = os.path.join(TASKS_DIR, f"{task_name}.json")
        self.source_type = source_type

        self.configure(fg_color=fg_color)

        # appearance mode
        self.appearance_mode = ctk.get_appearance_mode()
        self.sun_icon = sun_icon
        self.moon_icon = moon_icon
        self.plus_icon = plus_icon
        self.upload_icon = upload_icon
        self.folder_icon = folder_icon
        
        # layout
        self.grid_columnconfigure(0, weight=1)  # left panel
        self.grid_columnconfigure(1, weight=1)  # right panel
        self.grid_rowconfigure(0, weight=0)  # top bar
        self.grid_rowconfigure(1, weight=1)  # main content
        self.grid_rowconfigure(2, weight=0)  # bottom bar
        
        # top bar
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        topbar.grid_columnconfigure(0, weight=1)
        self.mode_btn = ctk.CTkButton(
            topbar,
            image=self.sun_icon if self.appearance_mode == "Dark" else self.moon_icon,
            text="",
            command=self.toggle_mode,
            fg_color=icon_color,
            width=32, height=32,
            corner_radius=8,
        )
        self.mode_btn.grid(row=0, column=1, sticky="e", padx=20)

        # left: input area
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        self.left_frame.grid_columnconfigure(0, weight=1)

        if source_type == "drive":
            self.setup_drive_frame()
        else:
            self.setup_local_frame()

        # right: label upload and preview
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # label txt section
        label_section = ctk.CTkFrame(right_frame, fg_color="transparent")
        label_section.pack(fill="x", padx=10, pady=10)
        label_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(label_section, text="Label", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.upload_btn = ctk.CTkButton(
            label_section, 
            text="Upload", 
            image=self.upload_icon, 
            width=100, 
            command=self.upload_txt, 
            fg_color=blue_color,
            hover_color=blue_color,
            text_color="#ffffff",
            compound="left"
        )
        self.upload_btn.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # label preview
        ctk.CTkLabel(right_frame, text="Preview", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        
        preview_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # scrollbar and listbox
        list_container = ctk.CTkFrame(preview_frame, fg_color="transparent")
        list_container.pack(fill="both", expand=True)
        
        # scrollbar first
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        # listbox
        self.label_preview = tk.Listbox(
            list_container,
            height=8,
            font=("TkDefaultFont", 10),
            selectmode="single",
            relief="flat",
            bg="#ffffff" if self.appearance_mode == "Light" else "#1e1e1e",
            fg="#18181b" if self.appearance_mode == "Light" else "#f5f5f5",
            selectbackground="#3b82f6",
            selectforeground="#ffffff",
            borderwidth=0,
            highlightthickness=0
        )
        self.label_preview.pack(side="left", fill="both", expand=True)
        
        # scrollbar and listbox
        self.label_preview.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.label_preview.yview)

        # bottom: status and buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        bottom_frame.grid_columnconfigure(1, weight=1)  # center space
        
        # status message
        self.status = ctk.CTkLabel(bottom_frame, text="")
        self.status.grid(row=0, column=1, sticky="ew")
        
        # buttons
        self.back_btn = ctk.CTkButton(
            bottom_frame,
            text="Back",
            fg_color=gray_color,
            hover_color=gray_color,
            text_color="white",
            command=self.go_back
        )
        self.back_btn.grid(row=0, column=0, padx=10)
        
        self.next_btn = ctk.CTkButton(
            bottom_frame,
            text="Next",
            fg_color=green_color,
            hover_color=green_color,
            text_color="white",
            command=self.save_and_next
        )
        self.next_btn.grid(row=0, column=2, padx=10)

        # loading view
        self.loading_label = ctk.CTkLabel(bottom_frame, text="", font=ctk.CTkFont(size=14))
        self.loading_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        # if existing json data, pre-fill
        if os.path.exists(self.task_path):
            try:
                with open(self.task_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    if "folder_id" in data:
                        self.folder_id = data["folder_id"]
                        if hasattr(self, 'drive_entry'):
                            self.drive_entry.insert(0, self.folder_id)
                    if "local_folder_path" in data:
                        self.local_folder_path = data["local_folder_path"]
                        if hasattr(self, 'folder_entry'):
                            self.folder_entry.insert(0, self.local_folder_path)
                    if "labels" in data and isinstance(data["labels"], list):
                        self.labels = data["labels"]
                    if "label_dict" in data and isinstance(data["label_dict"], dict):
                        self.label_dict = data["label_dict"]
                        self.label_preview.delete(0, tk.END)
                        for label in self.labels:
                            self.label_preview.insert(tk.END, label)
                        self.status.configure(text=f"{len(self.labels)} labels loaded")
            except Exception as e:
                pass

        # image related attributes
        self.base_image = None  # for original image

    def setup_drive_frame(self):
        """Drive input area"""
        self.drive_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.drive_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.drive_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.drive_frame, text="Google Drive Folder ID", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(10, 2))
        self.drive_entry = ctk.CTkEntry(self.drive_frame, placeholder_text="Input Folder ID here...", takefocus=False)
        self.drive_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))

    def setup_local_frame(self):
        """Local input area"""
        self.local_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.local_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.local_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.local_frame, text="Folder Path", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(10, 2))
        self.folder_frame = ctk.CTkFrame(self.local_frame, fg_color="transparent")
        self.folder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.folder_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ctk.CTkEntry(self.folder_frame, placeholder_text="Select folder...", takefocus=False)
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        button_frame = ctk.CTkFrame(self.folder_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="ew")
        
        self.folder_btn = ctk.CTkButton(
            button_frame,
            image=self.folder_icon,
            text="",
            width=32,
            command=self.select_folder,
            fg_color=icon_color
        )
        self.folder_btn.grid(row=0, column=0, padx=(0, 5))

    def select_folder(self):
        """select local folder"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.local_folder_path = folder_path
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)

    def save_and_next(self):
        """save settings and move to next step"""
        # load existing data (if exists)
        existing_data = {
            "folder_id": "",
            "local_folder_path": "",
            "source_type": self.source_type,
            "labels": [],
            "label_dict": {}
        }
        if os.path.exists(self.task_path):
            try:
                with open(self.task_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load existing task data: {str(e)}")

        if self.source_type == "drive":
            folder_id = self.drive_entry.get().strip()
            if not folder_id:
                self.status.configure(text="Please input Folder ID.")
                return
            # Update folder_id only in Drive mode
            existing_data["folder_id"] = folder_id
        else:  # local
            folder_path = self.folder_entry.get().strip() if hasattr(self, 'folder_entry') else ""
            if not folder_path:
                self.status.configure(text="Please select a folder.")
                return
            # Update local_folder_path only in Local mode
            existing_data["local_folder_path"] = folder_path

        if not self.labels:
            self.status.configure(text="Please upload Label txt.")
            return
        
        # Update common data
        existing_data.update({
            "source_type": self.source_type,
            "labels": self.labels,
            "label_dict": self.label_dict
        })
        
        # Save file
        with open(self.task_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        self.destroy()
        folder_path = existing_data["folder_id"] if self.source_type == "drive" else existing_data["local_folder_path"]
        
        # Set annotation path based on source type
        annotation_base = os.path.join(self.ANNOTATIONS_DIR, f"{self.task_name}")
        annotation_paths = {
            "yolo_local": f"{annotation_base}_annotation_yolo_local.json",
            "yolo_drive": f"{annotation_base}_annotation_yolo_drive.json",
            "coco_local": f"{annotation_base}_annotation_coco_local.json",
            "coco_drive": f"{annotation_base}_annotation_coco_drive.json"
        }
        
        # Select appropriate annotation paths based on source type
        if self.source_type == "drive":
            yolo_annotation_path = annotation_paths["yolo_drive"]
            coco_annotation_path = annotation_paths["coco_drive"]
        else:  # local
            yolo_annotation_path = annotation_paths["yolo_local"]
            coco_annotation_path = annotation_paths["coco_local"]
        
        from dialog.imagedialog import ImageDialog
        ImageDialog(
            self.master, 
            folder_path, 
            self.labels, 
            self.task_path, 
            self.label_dict, 
            source_type=self.source_type,
            yolo_annotation_path=yolo_annotation_path,
            coco_annotation_path=coco_annotation_path
        )

    def toggle_mode(self):
        """toggle theme"""
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        is_dark = new_mode == "Dark"
        
        # update colors according to theme
        self.mode_btn.configure(
            image=self.sun_icon if is_dark else self.moon_icon,
            fg_color=icon_color
        )
        
        # update main frame colors
        self.configure(fg_color=fg_color)
        
        # update input fields (according to source type)
        if self.source_type == "drive" and hasattr(self, 'drive_entry'):
            self.drive_entry.configure(
                fg_color=icon_color,
                text_color=text_color,
                placeholder_text_color=placeholder_color
            )
        elif self.source_type == "local" and hasattr(self, 'folder_entry'):
            self.folder_entry.configure(
                fg_color=icon_color,
                text_color=text_color,
                placeholder_text_color=placeholder_color
            )
            
            # update file list listbox
            if hasattr(self, 'files_preview'):
                self.files_preview.configure(
                    bg="#ffffff" if not is_dark else "#1e1e1e",
                    fg="#18181b" if not is_dark else "#f5f5f5"
                )
        
        # update upload button
        self.upload_btn.configure(
            fg_color=blue_color,
            hover_color=blue_color,
            text_color="#ffffff"
        )
        
        # update label preview
        self.label_preview.configure(
            bg="#ffffff" if not is_dark else "#1e1e1e",
            fg="#18181b" if not is_dark else "#f5f5f5"
        )
        
        # update buttons
        self.back_btn.configure(
            fg_color=gray_color
        )
        self.next_btn.configure(
            fg_color=green_color
        )
        
        # update status label
        if hasattr(self, 'status'):
            self.status.configure(text_color=text_color)

    def upload_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not path:
            return
        self.label_txt_path = path
        self.labels = []  # list for product names only
        self.label_dict = {}  # dictionary with number as key and product name as value
        
        try:
            with open(path, "r", encoding="utf-8-sig") as f:  # change to utf-8-sig to handle BOM
                lines = f.readlines()
                
                # check if first line is header and process all lines
                for line in lines:
                    line = line.strip()
                    if not line:  # skip empty lines
                        continue
                        
                    # process lines that are not header
                    if not ("사진 번호" in line and "상품명" in line):
                        parts = line.split(None, 1)  # split by first whitespace
                        if len(parts) == 2:
                            number, product_name = parts
                            if number.isdigit():
                                number = str(int(number))  # remove leading zeros
                                self.labels.append(product_name)
                                self.label_dict[number] = product_name
            
            # if existing tasks.json file, load data
            if os.path.exists(self.task_path):
                try:
                    with open(self.task_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            if "labels" in data and isinstance(data["labels"], list):
                                # merge new labels with existing labels
                                existing_labels = set(data["labels"])
                                new_labels = set(self.labels)
                                self.labels = list(existing_labels | new_labels)  # 중복 제거하여 합치기
                            if "label_dict" in data and isinstance(data["label_dict"], dict):
                                # merge new label_dict with existing label_dict
                                self.label_dict.update(data["label_dict"])
                except Exception as e:
                    print(f"Warning: Failed to load existing task data: {str(e)}")
            
            # update label preview - keep original text format
            self.label_preview.delete(0, tk.END)
            self.label_preview.insert(tk.END, "사진 번호        상품명")  # add header
            for number, label in sorted(self.label_dict.items(), key=lambda x: int(x[0])):
                # format number as 2 digits
                formatted_number = f"{int(number):02d}"
                # add enough spaces between number and label
                self.label_preview.insert(tk.END, f"{formatted_number}        {label}")
            
            self.status.configure(text=f"{len(self.labels)} labels loaded")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load labels: {str(e)}")

    def go_back(self):
        """go back"""
        if self.on_back_to_main:
            self.destroy()
            self.on_back_to_main()

    def load_label_data(self):
        if os.path.exists(self.label_txt_path):
            with open(self.label_txt_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    return data.get("images", [])
                except:
                    return []
        return []