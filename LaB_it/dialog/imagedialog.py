import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import io
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import json
from CTkMenuBar import *
import tkinter.colorchooser as colorchooser
import datetime
from setting import *

class ImageDialog(ctk.CTkToplevel):
    def __init__(self, master, folder_id, labels, task_path, label_dict, source_type="drive", yolo_annotation_path=None, coco_annotation_path=None):
        super().__init__(master)
        
        self.title("LaB_it-Image Labeling")
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = int(screen_w * 0.8)
        win_h = int(screen_h * 0.8)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.resizable(True, True)
        
        # min size (800x600)
        self.minsize(800, 600)
        
        # initialize variables
        self.folder_id = folder_id
        self.labels = labels
        self.task_path = task_path
        self.label_dict = label_dict
        self.source_type = source_type
        self.task_name = os.path.basename(task_path).replace('.json', '')
        self.loading_complete = False
        self.loading_lock = False
        self.left_panel_visible = True
        self.scale = 1.0
        self.initial_scale = None
        self.cur_image_pil = None
        self.photo = None
        self.image_x = 0
        self.image_y = 0
        self.has_unsaved_mask = False
        self.toast_label = None
        self._toast_after = None
        self.current_tool = "cursor"
        self.annotations = []
        self.yolo_annotation_path = yolo_annotation_path
        self.coco_annotation_path = coco_annotation_path
        self.current_rect = None
        self.selected_annotation_idx = None
        self.polygon_points = []
        self.temp_line = None
        self.polygon_lines = []
        self.drag_mode = False
        self.polygon_mode = False
        self.show_guides = True
        
        # set theme
        self.appearance_mode = ctk.get_appearance_mode()
        
        # initialize basic properties
        self.label_data = []
        
        # predefined color palette
        self.predefined_colors = predefined_color
        
        # initialize colors
        self.label_colors = {}
        self.initialize_colors()
        
        # UI related properties
        self.files = []
        self.cur_image_name = None
        self.cur_bbox = []
        self.cur_masks = []
        self.gallery_window = None
        self.toast_label = None
        self.toast_label = None
        self.current_tool = "cursor"
        self.annotations = []
        self.yolo_annotation_path = yolo_annotation_path
        self.coco_annotation_path = coco_annotation_path
        self.current_rect = None
        self.selected_annotation_idx = None
        self.polygon_points = []
        self.temp_line = None
        self.polygon_lines = []
        
        # main layout
        self.grid_columnconfigure(0, weight=0, minsize=0)  # left panel
        self.grid_columnconfigure(1, weight=1)  # main canvas
        self.grid_columnconfigure(2, weight=0)  # right panel
        self.grid_rowconfigure(1, weight=1)

        # set theme
        self.configure(fg_color=fg_color)
        
        # load icons
        self.load_icons()
        
        # setup left panel
        self.setup_left_panel()
        
        # setup toolbar
        self.setup_toolbar()
        
        # setup right panel
        self.setup_right_panel()
        
        # setup main canvas
        self.setup_main_canvas()

        # setup floating navigation
        self.setup_floating_nav()
        
        # load image list
        self.after(100, self.load_image_list)

        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind("<Control-c>", lambda e: self.set_cursor_mode())
        self.bind("<Control-b>", lambda e: self.set_box_mode())
        self.bind("<Control-p>", lambda e: self.set_polygon_mode())
        self.bind("<Control-s>", lambda e: self.save_task_json())
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def list_images_in_folder(self, folder_id):
        credentials = service_account.Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build('drive', 'v3', credentials=credentials)
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        results = service.files().list(q=query, pageSize=1000,
                                    fields="files(id, name)").execute()
        files = results.get('files', [])
        return [(f["name"], f["id"]) for f in files]

    def get_image_from_drive(self, file_id):
        credentials = service_account.Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build('drive', 'v3', credentials=credentials)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return Image.open(fh)

    def initialize_colors(self):
        """initialize colors and update task.json"""
        try:
            # read task.json
            with open(self.task_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
            
            # create colors object if not exists
            if "colors" not in task_data:
                task_data["colors"] = {}
            
            # check and update colors for each label
            for i, label in enumerate(self.labels):
                if label not in task_data["colors"]:
                    # assign colors from predefined palette sequentially
                    color_idx = i % len(self.predefined_colors)
                    task_data["colors"][label] = self.predefined_colors[color_idx]
            
            # use deep copy
            self.label_colors = task_data["colors"].copy()
            
            # update task.json file
            with open(self.task_path, "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to initialize colors: {str(e)}")
            self.label_colors = {}
            for i, label in enumerate(self.labels):
                color_idx = i % len(self.predefined_colors)
                self.label_colors[label] = self.predefined_colors[color_idx]

    def show_guide_lines(self, event):
        """Show guide lines at mouse position"""
        
        # Get the actual canvas coordinates
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        mouse_x = event.x_root - canvas_x
        mouse_y = event.y_root - canvas_y
        
        if self.current_tool != "polygon":
            self.canvas.delete("guide_line")
            return
        
        if not hasattr(self, 'photo') or self.photo is None:
            self.canvas.delete("guide_line")
            return
        
        # Use relative coordinates for guide lines
        x = mouse_x
        y = mouse_y
        
        if not (self.image_x <= x <= self.image_x + self.photo.width() and
                self.image_y <= y <= self.image_y + self.photo.height()):
            self.canvas.delete("guide_line")
            return
        
        self.canvas.delete("guide_line")
        
        # Use a gray color
        guide_color = "#D3D3D3" if self.appearance_mode == "Dark" else "#808080"
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Ensure canvas has size
        if canvas_width <= 1 or canvas_height <= 1:
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
        
        # Draw vertical line
        self.canvas.create_line(
            x, 0, x, canvas_height,
            fill=guide_color, dash=(4, 4), width=2, tags="guide_line"
        )
        
        # Draw horizontal line
        self.canvas.create_line(
            0, y, canvas_width, y,
            fill=guide_color, dash=(4, 4), width=2, tags="guide_line"
        )
        
        # Ensure proper z-order
        self.canvas.tag_lower("main_image")
        self.canvas.tag_raise("annotation")
        self.canvas.tag_raise("guide_line")

    def load_icons(self):
        """load icon images"""
        self.icons = {
            "sun": sun_icon,
            "moon": moon_icon,
            "cursor": cursor_icon,
            "box": box_icon,
            "polygon": polygon_icon,
            "eraser": erase_icon,
            "zoom_in": zoom_in_icon,
            "zoom_out": zoom_out_icon,
            "rotate": rotate_icon,
            "save": save_icon,
            "close": close_icon,
            "arrow_double_right": arrow_double_icon,
            "arrow_left": arrow_left_icon,
            "arrow_right": arrow_right_icon,
            "plus": plus_icon,
            "flash": flash_icon,
            "download": download_icon,
        }

    def setup_left_panel(self):
        """setup left panel"""
        # main panel
        self.left_panel = ctk.CTkFrame(self, fg_color=panel_color, width=300, corner_radius=10)  # rounded corners
        self.left_panel.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(10, 5), pady=10)
        self.left_panel.grid_propagate(False)
        
        # mini panel (hidden when closed)
        self.mini_panel = ctk.CTkFrame(self, fg_color=panel_color, width=50, corner_radius=10)  # rounded corners
        self.mini_panel.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(10, 5), pady=10)
        self.mini_panel.grid_remove()  # hidden initially
        self.mini_panel.pack_propagate(False)
        
        # add open button to mini panel
        self.open_btn = ctk.CTkButton(
            self.mini_panel,
            text="",
            image=self.icons["arrow_double_right"],
            width=30,
            height=30,
            command=self.toggle_left_panel,
            fg_color=icon_color,
            hover_color=icon_color
        )
        self.open_btn.pack(pady=5)
        
        # main panel contents
        # top header
        header_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text="Labels",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # close button
        close_btn = ctk.CTkButton(
            header_frame,
            text="",
            image=self.icons["close"],
            width=30,
            height=30,
            command=self.toggle_left_panel,
            fg_color=icon_color,
            hover_color=icon_color
        )
        close_btn.pack(side="right")
        
        # add new label frame
        add_label_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        add_label_frame.pack(fill="x", padx=10, pady=5)
        
        # new label input field
        self.new_label_entry = ctk.CTkEntry(
            add_label_frame,
            placeholder_text="Add new label",
            font=ctk.CTkFont(size=13),
            height=35,
            fg_color=("#ffffff", "#1e1e1e"),
            text_color=("#18181b", "#f5f5f5"),
            placeholder_text_color=("#64748b", "#9ca3af")
        )
        self.new_label_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # add button
        add_btn = ctk.CTkButton(
            add_label_frame,
            text="",
            image=self.icons["plus"],
            width=35,
            height=35,
            command=self.add_new_label,
            fg_color="transparent"
        )
        add_btn.pack(side="right")
        
        # add Auto Labeling text (left alignment)
        auto_label_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        auto_label_frame.pack(fill="x", padx=10, pady=(5,0))
        
        ctk.CTkLabel(
            auto_label_frame,
            text="Auto Labeling",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x")

        # current image label input field
        self.label_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="Label will be auto-extracted", 
            font=ctk.CTkFont(size=13),
            height=35,
            fg_color=("#ffffff", "#1e1e1e"),
            text_color=("#18181b", "#f5f5f5"),
            placeholder_text_color=("#64748b", "#9ca3af")
        )
        self.label_entry.pack(fill="x", padx=10, pady=5)
        
        # label list container
        self.label_list_container = ctk.CTkFrame(self.left_panel, fg_color=("#f3f4f6", "#6b7480"), corner_radius=0)
        self.label_list_container.pack(fill="x", expand=False, padx=10, pady=5)
        
        # label list title
        ctk.CTkLabel(
            self.label_list_container,
            text="Available Labels",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=5)
        
        # label list scroll area
        label_scroll = ctk.CTkScrollableFrame(self.label_list_container, height=150)
        label_scroll.pack(fill="x", expand=False, padx=5, pady=5)
        
        # inner frame to hold labels
        self.label_list = ctk.CTkFrame(label_scroll, fg_color="transparent")
        self.label_list.pack(fill="x", expand=True)
        
        # separator
        separator = ctk.CTkFrame(self.left_panel, height=2, fg_color=gray_color)
        separator.pack(fill="x", padx=10, pady=10)
        
        # annotation list container
        annotation_container = ctk.CTkFrame(self.left_panel, fg_color=panel_color, corner_radius=0)
        annotation_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # annotation list title
        ctk.CTkLabel(
            annotation_container,
            text="Annotations",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=5)
        
        # scrollable frame for annotation list
        self.annotation_scroll = ctk.CTkScrollableFrame(annotation_container)
        self.annotation_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # update label list
        self.update_label_list()
        
        # update annotation list
        self.update_annotation_list()

    def add_new_label(self):
        """add new label"""
        new_label = self.new_label_entry.get().strip()
        if not new_label:
            self.show_toast("Please enter a label name", fg_color=("#ef4444", "#dc2626"))
            return
            
        if new_label in self.labels:
            self.show_toast("Label already exists", fg_color=("#ef4444", "#dc2626"))
            return
            
        # read task.json file
        try:
            with open(self.task_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
        except Exception as e:
            self.show_toast(f"Failed to load task data: {str(e)}", fg_color=("#ef4444", "#dc2626"))
            return
            
        # add new label and color
        if "labels" not in task_data:
            task_data["labels"] = []
        if "colors" not in task_data:
            task_data["colors"] = {}
            
        task_data["labels"].append(new_label)
        if new_label not in task_data["colors"]:
            task_data["colors"][new_label] = self.generate_random_color()
            
        # save file
        try:
            with open(self.task_path, "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
                
            # update memory
            self.labels = task_data["labels"]
            self.label_colors = task_data["colors"]
            
            # update UI
            self.new_label_entry.delete(0, 'end')
            self.update_label_list()
            self.show_toast("New label added!")
        except Exception as e:
            self.show_toast(f"Failed to save task data: {str(e)}", fg_color=("#ef4444", "#dc2626"))

    def show_color_picker(self, label):
        """show color picker dialog"""
        color = colorchooser.askcolor(
            color=self.label_colors[label],
            title=f"Choose color for {label}"
        )
        if color[1]:  # color is (RGB, hex)
            # read task.json file
            try:
                with open(self.task_path, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                    
                if "colors" not in task_data:
                    task_data["colors"] = {}
                    
                # update color
                task_data["colors"][label] = color[1]
                
                # save file
                with open(self.task_path, "w", encoding="utf-8") as f:
                    json.dump(task_data, f, ensure_ascii=False, indent=2)
                    
                # update memory
                self.label_colors[label] = color[1]
                
                # update UI
                self.update_label_list()
            except Exception as e:
                self.show_toast(f"Failed to save color: {str(e)}", fg_color=("#ef4444", "#dc2626"))

    def update_label_list(self):
        """update label list"""
        # remove existing items
        for widget in self.label_list.winfo_children():
            widget.destroy()
            
        # load color info from task.json
        try:
            with open(self.task_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                if "colors" in task_data:
                    self.label_colors = task_data["colors"]
                else:
                    task_data["colors"] = {}
                    # generate color for non-existing labels
                    for label in self.labels:
                        if label not in self.label_colors:
                            self.label_colors[label] = self.generate_random_color()
                            task_data["colors"][label] = self.label_colors[label]
                    # save file
                    with open(self.task_path, "w", encoding="utf-8") as f:
                        json.dump(task_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to load/save color data: {str(e)}")
        
        # display label list
        for i, label in enumerate(self.labels):
            # label item frame
            item_frame = ctk.CTkFrame(self.label_list, fg_color=("#f3f4f6", "#27272a"), corner_radius=0)
            item_frame.pack(fill="x", pady=2, padx=5)  # add x-axis margin
            
            # label name
            ctk.CTkLabel(
                item_frame,
                text=label,
                font=ctk.CTkFont(size=13),
                text_color=("#18181b", "#f5f5f5"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=5)  # add left padding
            
            # color display and selection button
            color_btn = ctk.CTkButton(
                item_frame,
                text="",
                width=20,
                height=20,
                fg_color=self.label_colors.get(label, self.generate_random_color()),
                hover_color=self.label_colors.get(label, self.generate_random_color()),
                command=lambda l=label: self.show_color_picker(l),
                corner_radius=0
            )
            color_btn.pack(side="right", padx=5)

    def generate_random_color(self):
        """generate random color"""
        import random
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def toggle_left_panel(self):
        """toggle left panel"""
        if self.left_panel_visible:
            self.left_panel.grid_remove()
            self.mini_panel.grid()
            self.left_panel_visible = False
        else:
            self.mini_panel.grid_remove()
            self.left_panel.grid()
            self.left_panel_visible = True
            
        # if there is an image, center align
        if self.cur_image_pil:
            self.display_image(self.cur_image_pil)

    def setup_toolbar(self):
        """setup toolbar"""
        toolbar = ctk.CTkFrame(self, fg_color=panel_color, height=40)
        toolbar.grid(row=0, column=1, sticky="ew", pady=10, padx=10)
        toolbar.grid_propagate(False)
        
        # go back to previous window button
        prev_btn = ctk.CTkButton(
            toolbar,
            text="Prev Window",
            image=self.icons["arrow_left"],
            font=ctk.CTkFont(size=13),
            width=100,
            height=28,
            fg_color="transparent",
            text_color=text_color,
            hover_color=icon_color,
            compound="left",
            command=self.go_to_setup
        )
        prev_btn.pack(side="left", padx=(10, 20))
        
        # display image number
        self.image_counter = ctk.CTkLabel(
            toolbar,
            text="0 / 0",
            font=ctk.CTkFont(size=14)
        )
        self.image_counter.pack(side="left", padx=10)
        
        # add image selection option menu
        ctk.CTkLabel(toolbar, text="Select Image:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
        self.image_option = ctk.CTkOptionMenu(
            toolbar,
            values=["Loading..."],
            command=self.on_image_option_select,
            width=300,
            fg_color=("#ffffff", "#363434"),
            button_color=("#babbbf", "#27272a"),
            text_color=("#18181b", "#ffffff"),
            dropdown_fg_color=("#ffffff", "#363434"),
        )
        self.image_option.pack(side="left")

        # right buttons
        right_btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_btn_frame.pack(side="right", padx=10)
        
        # theme change button
        self.theme_btn = ctk.CTkButton(
            right_btn_frame,
            image=self.icons["sun" if self.appearance_mode == "Dark" else "moon"],
            text="",
            command=self.toggle_theme,
            width=32, height=32,
            fg_color=icon_color,
            hover_color=icon_color,
            corner_radius=8
        )
        self.theme_btn.pack(side="left", pady=5)

    def setup_right_panel(self):
        """setup right tool panel"""
        right_panel = ctk.CTkFrame(self, fg_color=panel_color, width=50, corner_radius=10)
        right_panel.grid(row=0, column=2, rowspan=3, sticky="nsew", pady=10, padx=(5, 10))
        right_panel.grid_propagate(False)
        right_panel.pack_propagate(False)
        
        # setup tool buttons
        tools = [
            ("cursor", self.set_cursor_mode),
            ("box", self.set_box_mode),
            ("polygon", self.set_polygon_mode),
            ("zoom_in", self.zoom_in),
            ("zoom_out", self.zoom_out),
            ("rotate", self.rotate_image),
            ("save", self.save_task_json),
            ("download", self.show_download_dialog)
        ]
        
        self.tool_buttons = {}
        self.selectable_tools = ["cursor", "box", "polygon"]
        
        # tool buttons container
        tool_buttons_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        tool_buttons_frame.pack(pady=5)
        
        for icon_name, command in tools:
            btn = ctk.CTkButton(
                tool_buttons_frame,
                text="",
                image=self.icons[icon_name],
                width=30,
                height=30,
                command=command,
                fg_color="transparent" if icon_name not in self.selectable_tools else 
                         ("#3b82f6", "#2563eb") if icon_name == "cursor" else "transparent",
                hover_color=("#e5e7eb", "#374151") if icon_name not in self.selectable_tools else
                           ("#2563eb", "#1d4ed8"),
            )
            btn.pack(pady=2)
            self.tool_buttons[icon_name] = btn

    def show_download_dialog(self):
        """
        open a download dialog
        """
        from dialog.formatselectdialog import FormatSelectDialog
        FormatSelectDialog(self, self.task_name, self.download_json)

    def set_cursor_mode(self):
        """set cursor mode"""
        self.current_tool = "cursor"
        self.drag_mode = False
        self.polygon_mode = False
        self.show_guides = False  # 커서 모드에서 가이드라인 비활성화
        self.canvas.config(cursor="arrow")
        self.canvas.tag_unbind("annotation", "<Enter>")
        self.canvas.tag_unbind("annotation", "<Leave>")
        self.canvas.tag_unbind("annotation", "<Button-1>")
        self.update_tool_buttons("cursor")

    def set_box_mode(self):
        """set box drawing mode"""
        self.current_tool = "box"
        self.drag_mode = True
        self.polygon_mode = False
        self.show_guides = False  # 박스 모드에서 가이드라인 비활성화
        self.canvas.config(cursor="crosshair")
        self.update_tool_buttons("box")

    def set_polygon_mode(self):
        """set polygon drawing mode"""
        self.current_tool = "polygon"
        self.drag_mode = False
        self.polygon_mode = True
        self.show_guides = True  # 폴리곤 모드에서 가이드라인 활성화
        self.canvas.config(cursor="crosshair")
        self.update_tool_buttons("polygon")

    def update_tool_buttons(self, selected_tool):
        """update tool buttons"""
        for tool_name in self.selectable_tools:
            if tool_name == selected_tool:
                self.tool_buttons[tool_name].configure(
                    fg_color=("#3b82f6", "#2563eb"),
                    hover_color=("#2563eb", "#1d4ed8")
                )
            else:
                self.tool_buttons[tool_name].configure(
                    fg_color="transparent",
                    hover_color=("#e5e7eb", "#374151")
                )

    def setup_main_canvas(self):
        """setup main canvas"""
        canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        canvas_frame.grid(row=1, column=1, sticky="nsew", padx=5)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#1e1e1e",
            highlightthickness=0,
            cursor="arrow"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # canvas event bindings
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)
        
        # Bind both canvas and main window for mouse motion
        self.canvas.bind("<Motion>", self.show_guide_lines)
        self.bind_all("<Motion>", self.show_guide_lines)
        
        # mouse wheel event bindings (zoom in/out)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # variables for image dragging
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
        # loading label
        self.loading_label = ctk.CTkLabel(
            canvas_frame,
            text="Loading images...",
            font=ctk.CTkFont(size=16)
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

    def zoom_in(self):
        """zoom in"""
        if self.cur_image_pil:
            self.scale = min(self.scale * 1.2, 5.0)
            self.display_image(self.cur_image_pil)
            self.show_toast("Zoomed in")

    def zoom_out(self):
        """zoom out"""
        if self.cur_image_pil:
            self.scale = max(self.scale / 1.2, 0.2)
            self.display_image(self.cur_image_pil)
            self.show_toast("Zoomed out")

    def rotate_image(self):
        """rotate image"""
        if self.cur_image_pil:
            self.cur_image_pil = self.cur_image_pil.rotate(90, expand=True)
            self.update_image()
            self.show_toast("Image rotated")

    def update_image(self):
        """update image (reflect zoom in/out/rotation)"""
        if self.cur_image_pil:
            self.display_image(self.cur_image_pil)

    def load_image_list(self):
        """load image list asynchronously"""
        try:
            if self.source_type == "drive":
                self.files = self.list_images_in_folder(self.folder_id)
            else:  # local
                self.files = []
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    self.files.extend([(f, os.path.join(self.folder_id, f)) 
                                     for f in os.listdir(self.folder_id) 
                                     if f.lower().endswith(ext)])
            
            if self.files:
                self.image_option.configure(values=[name for name, _ in self.files])
                self.image_option.set(self.files[0][0])
                self.loading_label.configure(text="")
                self.loading_complete = True
                self.load_image(self.files[0][0], self.files[0][1])
                
                # update image counter
                self.update_image_counter(0)
            else:
                self.loading_label.configure(text="No images found in the folder")
        except Exception as e:
            self.loading_label.configure(text=f"Error loading images: {str(e)}")

    def update_image_counter(self, current_index):
        """update image counter"""
        total_images = len(self.files)
        self.image_counter.configure(text=f"{current_index + 1} / {total_images}")

    def load_image(self, name, file_id):
        """load image and display"""
        if self.loading_lock:
            return
        self.loading_lock = True
        try:
            self.cur_image_name = name
            self.has_unsaved_mask = False
            self.annotations = []
            
            # initialize zoom state
            self.initial_scale = None
            self.scale = 1.0
            
            # extract label from filename
            label = self.extract_label_from_filename(name)
            self.label_entry.delete(0, 'end')
            self.label_entry.insert(0, label)
            
            self.loading_label.configure(text="Loading Image...")
            self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
            self.update()
            
            # load image differently based on source type
            if self.source_type == "drive":
                pil_img = self.get_image_from_drive(file_id)
            else:  # local
                pil_img = Image.open(file_id)
                
            self.cur_image_pil = pil_img
            self.display_image(pil_img)
            self.loading_label.place_forget()
            
            # load YOLO annotation file
            if self.yolo_annotation_path and os.path.exists(self.yolo_annotation_path):
                try:
                    with open(self.yolo_annotation_path, "r", encoding="utf-8") as f:
                        yolo_data = json.load(f)
                        if isinstance(yolo_data, dict):
                            self.label_data = yolo_data.get("images", [])
                            
                            # find annotations for current image
                            for item in self.label_data:
                                if isinstance(item, dict) and item.get("image_name") == name:
                                    # load all bbox info for current image
                                    if "annotations" in item:
                                        self.annotations = item["annotations"]
                                        # display all annotations
                                        self.draw_all_annotations()
                                    break
                except Exception as e:
                    print(f"Warning: Failed to load YOLO annotation: {str(e)}")
                    self.show_toast(f"Failed to load annotations: {str(e)}", fg_color=("#ef4444", "#dc2626"))
        finally:
            self.loading_lock = False

    def draw_all_annotations(self):
        """draw all annotations"""
        for i, annotation in enumerate(self.annotations):
            bbox = annotation["bbox"]
            label = annotation["label"]
            
            # draw with color of corresponding label
            box_color = self.label_colors.get(label, "#3b82f6")
            
            if annotation.get("type", "box") == "box":
                # draw box (convert image coordinates to canvas coordinates)
                canvas_x1 = self.image_x + bbox[0] * self.scale
                canvas_y1 = self.image_y + bbox[1] * self.scale
                canvas_x2 = self.image_x + bbox[2] * self.scale
                canvas_y2 = self.image_y + bbox[3] * self.scale
                
                # create unique tags
                unique_tags = ("annotation", f"id:{i}", f"type:box")
                
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline=box_color,
                    width=2,
                    tags=unique_tags
                )
            else:  # polygon
                # convert polygon points to canvas coordinates
                points = annotation.get("points", [])
                canvas_points = []
                for point in points:
                    canvas_x = self.image_x + point[0] * self.scale
                    canvas_y = self.image_y + point[1] * self.scale
                    canvas_points.extend([canvas_x, canvas_y])
                
                if canvas_points:
                    # create unique tags
                    unique_tags = ("annotation", f"id:{i}", f"type:polygon")
                    
                    self.canvas.create_polygon(
                        canvas_points,
                        outline=box_color,
                        fill="",
                        width=2,
                        tags=unique_tags
                    )
        
        # update annotation list
        self.update_annotation_list()

    def extract_label_from_filename(self, filename):
        """extract label from filename"""
        # remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # find number pattern (e.g. "12) TAMS zero 오렌지 pet.01" from "TAMS zero 오렌지 pet.01")
        match = re.match(r'(\d+)\)(.*)', name_without_ext)
        if match:
            number = str(int(match.group(1)))  # remove leading zeros
            # find matching product name in label_dict
            if number in self.label_dict:
                return self.label_dict[number]
            else:
                # if no matching product name, extract from filename directly
                label_part = match.group(2).strip()
                if label_part:
                    # remove last number pattern (e.g. ".01")
                    label_part = re.sub(r'\.\d+$', '', label_part)
                    return label_part
        
        # if no number pattern, use filename as label
        cleaned_name = re.sub(r'\.\d+$', '', name_without_ext.strip())
        if cleaned_name:
            return cleaned_name
        
        # if all above fails, return first label
        return self.labels[0] if self.labels else ""

    def go_to_setup(self):
        """go back to setup dialog"""
        task_name = os.path.basename(self.task_path).replace('.json', '')
        self.destroy()
        # load current task's setup data to get source_type
        try:
            with open(self.task_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                source_type = task_data.get("source_type", "drive")  # default is "drive"
        except Exception as e:
            print(f"Warning: Failed to load task data: {str(e)}")
            source_type = "drive"  # use default value if error occurs
        from dialog.settingdialog import SetupDialog
        SetupDialog(self.master, task_name, lambda folder_id, labels: None, source_type)

    def deactivate_drag_mode(self):
        """deactivate drag mode"""
        self.drag_mode = False
        self.canvas.config(cursor="arrow")
        # show status message
        self.loading_label.configure(text="Cursor mode activated")
        self.loading_label.place(relx=0.5, rely=0.95, anchor="center")
        self.after(1500, lambda: self.loading_label.place_forget())  # hide message after 1.5 seconds

    def point_in_polygon(self, x, y, points):
        """check if point is inside polygon"""
        n = len(points)
        inside = False
        
        if n < 3:  # polygon needs at least 3 points
            return False
            
        j = n - 1
        for i in range(n):
            if (((points[i][1] > y) != (points[j][1] > y)) and
                (x < (points[j][0] - points[i][0]) * (y - points[i][1]) /
                     (points[j][1] - points[i][1]) + points[i][0])):
                inside = not inside
            j = i
            
        return inside

    def check_unsaved_mask(self):
        """check if there is unsaved masking or annotation"""
        if self.has_unsaved_mask and self.cur_bbox:
            self.show_toast("Unsaved mask exists!", 
                          fg_color=("#ef4444", "#dc2626"))  # red warning
            return True
            
        # check if current image's annotation is saved
        if self.cur_image_name:
            current_annotations = []
            for item in self.label_data:
                if isinstance(item, dict) and item.get("image_name") == self.cur_image_name:
                    current_annotations = item.get("annotations", [])
                    break
                    
            # compare number of current annotations and saved annotations
            if len(self.annotations) != len(current_annotations):
                self.show_toast("Unsaved annotation exists!", 
                              fg_color=("#ef4444", "#dc2626"))  # red warning
                return True
                
        return False

    def jump_to_next_unannotated(self):
        """jump to first unsaved image"""
        if self.check_unsaved_mask():
            return
            
        # get list of annotated images
        annotated_images = {item["image_name"] for item in self.label_data if isinstance(item, dict)}
        
        # find first unsaved image
        for i, (name, file_id) in enumerate(self.files):
            if name not in annotated_images:
                self.image_option.set(name)
                self.load_image(name, file_id)
                self.update_image_counter(i)  # update counter
                self.show_toast("Moved to first unsaved image")
                return
                
        self.show_toast("All images are saved!", fg_color=("#10b981", "#059669"))

    def show_app_version(self):
        """show app version info"""
        messagebox.showinfo("App Version", "SegT SAM Labeling Tool\nVersion: 1.0.0")

    def on_image_option_select(self, image_name):
        """called when image is selected"""
        if self.check_unsaved_mask():
            # if unsaved mask exists, revert to previous selection
            self.image_option.set(self.cur_image_name)
            return
            
        # find file_id and index of selected image
        for i, (name, file_id) in enumerate(self.files):
            if name == image_name:
                self.load_image(name, file_id)
                self.update_image_counter(i)
                break

    # --- image transition logic ---
    def show_prev_image(self):
        """move to previous image"""
        if self.check_unsaved_mask():
            return
            
        current = self.image_option.get()
        for i, (name, file_id) in enumerate(self.files):
            if name == current and i > 0:
                prev_name = self.files[i-1][0]
                self.image_option.set(prev_name)
                self.load_image(prev_name, self.files[i-1][1])
                self.update_image_counter(i-1)  # 카운터 업데이트
                break

    def show_next_image(self):
        """move to next image"""
        if self.check_unsaved_mask():
            return
            
        current = self.image_option.get()
        for i, (name, file_id) in enumerate(self.files):
            if name == current and i < len(self.files) - 1:
                next_name = self.files[i+1][0]
                self.image_option.set(next_name)
                self.load_image(next_name, self.files[i+1][1])
                self.update_image_counter(i+1)  # 카운터 업데이트
                break

    def toggle_theme(self):
        """toggle theme"""
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        is_dark = new_mode == "Dark"
        
        # update colors based on theme
        self.theme_btn.configure(
            image=self.icons["sun" if is_dark else "moon"],
            fg_color=("#ffffff", "#ede6e6")
        )
        
        # update main frame color
        self.configure(fg_color=("#ffffff", "#363434"))
        
        # update left panel color
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                if widget.winfo_x() == 10:  # left panel
                    widget.configure(fg_color=("#f3f4f6", "#6b7480"))
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkButton):
                            child.configure(
                                text_color=("#18181b", "#f5f5f5"),
                                hover_color=("#e5e7eb", "#374151")
                            )
        
        # update top toolbar color
        self.image_option.configure(
            fg_color=("#ffffff", "#363434"),
            button_color=("#babbbf", "#27272a"),
            text_color=("#18181b", "#ffffff"),
            dropdown_fg_color=("#ffffff", "#363434")
        )
        
        # update canvas background color
        self.canvas.configure(bg="#ffffff" if not is_dark else "#1e1e1e")

    def save_task_json(self):
        """save annotation data of current image"""
        if not self.cur_image_name:
            return
            
        # remove existing data of current image
        self.label_data = [item for item in self.label_data 
                          if isinstance(item, dict) and 
                          item.get("image_name") != self.cur_image_name]
        
        # image size
        img_width, img_height = self.cur_image_pil.size
        
        # create YOLO format data
        yolo_annotations = []
        for annotation in self.annotations:
            bbox = annotation["bbox"]
            label = annotation["label"]
            
            # calculate YOLO coordinates
            x_center = (bbox[0] + bbox[2]) / 2
            y_center = (bbox[1] + bbox[3]) / 2
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            # normalize coordinates
            x_center_norm = x_center / img_width
            y_center_norm = y_center / img_height
            width_norm = width / img_width
            height_norm = height / img_height
            
            # label index
            label_idx = self.labels.index(label) if label in self.labels else 0
            
            yolo_format = f"{label_idx} {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}"
            
            annotation_data = {
                "bbox": bbox,
                "label": label,
                "type": annotation.get("type", "box"),
                "yolo": yolo_format
            }
            
            # if polygon, save points info
            if annotation.get("type") == "polygon":
                annotation_data["points"] = annotation.get("points", [])
            
            yolo_annotations.append(annotation_data)
        
        # add current image data
        if self.annotations:  # only add if annotations exist
            image_data = {
                "image_name": self.cur_image_name,
                "annotations": yolo_annotations
            }
            self.label_data.append(image_data)
        
        # set suffix based on source type
        source_suffix = "_drive" if self.source_type == "drive" else "_local"
        
        # save YOLO format
        yolo_path = os.path.join(ANNOTATIONS_DIR, f"{self.task_name}_annotation_yolo{source_suffix}.json")
        try:
            with open(yolo_path, "w", encoding="utf-8") as f:
                json.dump({"images": self.label_data}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save YOLO annotation: {str(e)}")
            return

        # convert and save COCO format
        coco_path = os.path.join(ANNOTATIONS_DIR, f"{self.task_name}_annotation_coco{source_suffix}.json")
        try:
            if os.path.exists(coco_path):
                with open(coco_path, "r", encoding="utf-8") as f:
                    coco_data = json.load(f)
            else:
                coco_data = {
                    "info": {
                        "description": f"{self.task_name} dataset",
                        "version": "1.0",
                        "year": 2024,
                        "contributor": "LaB_it",
                        "date_created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "images": [],
                    "annotations": [],
                    "categories": []
                }
                # add category info
                for i, label_name in enumerate(self.labels):
                    coco_data["categories"].append({
                        "id": i + 1,
                        "name": label_name,
                        "supercategory": "object"
                    })

            # find or create image ID
            image_id = None
            for img in coco_data["images"]:
                if img["file_name"] == self.cur_image_name:
                    image_id = img["id"]
                    break
            
            if image_id is None and self.annotations:  # only add if annotations exist
                image_id = len(coco_data["images"]) + 1
                coco_data["images"].append({
                    "id": image_id,
                    "file_name": self.cur_image_name,
                    "width": img_width,
                    "height": img_height
                })
            elif not self.annotations and image_id is not None:  # only remove if annotations exist
                coco_data["images"] = [img for img in coco_data["images"] if img["id"] != image_id]

            if image_id is not None:
                # remove existing annotations
                coco_data["annotations"] = [
                    anno for anno in coco_data["annotations"]
                    if anno["image_id"] != image_id
                ]

                # add new annotations
                for annotation in self.annotations:
                    bbox = annotation["bbox"]
                    label = annotation["label"]
                    label_idx = self.labels.index(label) if label in self.labels else 0
                    
                    x, y = bbox[0], bbox[1]
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    area = width * height

                    annotation_id = len(coco_data["annotations"]) + 1
                    coco_annotation = {
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": label_idx + 1,
                        "bbox": [x, y, width, height],
                        "area": area,
                        "iscrowd": 0
                    }
                    
                    # if polygon, add segmentation info
                    if annotation.get("type") == "polygon":
                        points = annotation.get("points", [])
                        segmentation = []
                        for point in points:
                            segmentation.extend(point)
                        coco_annotation["segmentation"] = [segmentation]
                    else:
                        coco_annotation["segmentation"] = []
                    
                    coco_data["annotations"].append(coco_annotation)

            with open(coco_path, "w", encoding="utf-8") as f:
                json.dump(coco_data, f, ensure_ascii=False, indent=2)

            self.has_unsaved_mask = False
            # update annotation list
            self.update_annotation_list()
            self.show_toast("Annotations saved in YOLO and COCO formats!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save COCO annotation: {str(e)}")

    def get_current_label_color(self):
        """return color of current selected label"""
        label = self.label_entry.get().strip()
        if label in self.label_colors:
            return self.label_colors[label]
        # return default color (if label is not set or color is not set)
        return "#3b82f6"

    def end_draw(self, event):
        """end drag"""
        if self.current_tool == "cursor" and self.is_dragging:
            self.is_dragging = False
            self.canvas.config(cursor="arrow")
            return
            
        if not self.drag_mode or not self.current_rect or not self.cur_image_pil:
            return
            
        # last mouse position
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # limit to image area
        end_x = max(self.image_x, min(end_x, self.image_x + self.photo.width()))
        end_y = max(self.image_y, min(end_y, self.image_y + self.photo.height()))
        
        # normalize coordinates
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        
        # convert canvas coordinates to image coordinates
        x1 = (x1 - self.image_x) / self.scale
        y1 = (y1 - self.image_y) / self.scale
        x2 = (x2 - self.image_x) / self.scale
        y2 = (y2 - self.image_y) / self.scale
        
        # limit to image boundaries
        img_width, img_height = self.cur_image_pil.size
        x1 = max(0, min(x1, img_width))
        y1 = max(0, min(y1, img_height))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        
        # check minimum size
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return
        
        # set bbox coordinates
        bbox = [int(x1), int(y1), int(x2), int(y2)]
        
        # add new annotation
        annotation = {
            "bbox": bbox,
            "label": self.label_entry.get().strip(),
            "type": self.current_tool
        }
        self.annotations.append(annotation)
        self.has_unsaved_mask = True
        
        # keep current rect (do not delete)
        self.current_rect = None
        
        # update annotation list
        self.update_annotation_list()

    def draw(self, event):
        """dragging"""
        if self.current_tool == "cursor" and self.is_dragging:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            dx = x - self.drag_start_x
            dy = y - self.drag_start_y
            
            self.image_x += dx
            self.image_y += dy
            
            self.canvas.delete("all")
            self.canvas.create_image(self.image_x, self.image_y, anchor="nw", image=self.photo)
            
            # redraw all annotations
            self.draw_all_annotations()
            
            self.drag_start_x = x
            self.drag_start_y = y
            return
            
        if self.current_tool == "box" and self.current_rect:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            
            cur_x = max(self.image_x, min(cur_x, self.image_x + self.photo.width()))
            cur_y = max(self.image_y, min(cur_y, self.image_y + self.photo.height()))
            
            box_color = self.get_current_label_color()
            self.canvas.itemconfig(self.current_rect, outline=box_color)
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)

    def start_draw(self, event):
        """start dragging"""
        if not self.cur_image_pil:
            return
            
        if self.current_tool == "cursor":
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            if (self.image_x <= x <= self.image_x + self.photo.width() and
                self.image_y <= y <= self.image_y + self.photo.height()):
                self.is_dragging = True
                self.drag_start_x = x
                self.drag_start_y = y
                self.canvas.config(cursor="fleur")
            return
            
        # check if coordinates are within image area
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if not (self.image_x <= x <= self.image_x + self.photo.width() and
                self.image_y <= y <= self.image_y + self.photo.height()):
            return
            
        if self.current_tool == "polygon":
            # if first point, show start point
            if not self.polygon_points:
                self.polygon_points.append((x, y))
                self.canvas.create_oval(
                    x-3, y-3, x+3, y+3,
                    fill=self.get_current_label_color(),
                    tags="polygon_point"
                )
            else:
                # if start point, complete polygon
                start_x, start_y = self.polygon_points[0]
                if abs(x - start_x) < 10 and abs(y - start_y) < 10:
                    self.complete_polygon()
                else:
                    # add new point
                    self.polygon_points.append((x, y))
                    # show point
                    self.canvas.create_oval(
                        x-3, y-3, x+3, y+3,
                        fill=self.get_current_label_color(),
                        tags="polygon_point"
                    )
                    # draw line connecting previous point and current point
                    prev_x, prev_y = self.polygon_points[-2]
                    line = self.canvas.create_line(
                        prev_x, prev_y, x, y,
                        fill=self.get_current_label_color(),
                        width=2,
                        tags="polygon_line"
                    )
                    self.polygon_lines.append(line)
                    
                    # update temporary line
                    if self.temp_line:
                        self.canvas.delete(self.temp_line)
                    self.temp_line = self.canvas.create_line(
                        x, y, x, y,
                        fill=self.get_current_label_color(),
                        width=2,
                        dash=(4, 4)
                    )
        elif self.current_tool == "box":
            self.start_x = x
            self.start_y = y
            box_color = self.get_current_label_color()
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline=box_color,
                width=2
            )

    def on_mouse_move(self, event):
        """show temporary line when mouse moves"""
        if self.current_tool == "polygon" and self.polygon_points:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # delete previous temporary line
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            
            # show temporary line connecting last point and current mouse position
            last_x, last_y = self.polygon_points[-1]
            
            # if start point, connect to start point
            start_x, start_y = self.polygon_points[0]
            if abs(x - start_x) < 10 and abs(y - start_y) < 10:
                x, y = start_x, start_y
            
            self.temp_line = self.canvas.create_line(
                last_x, last_y, x, y,
                fill=self.get_current_label_color(),
                width=2,
                dash=(4, 4)  # dashed line
            )

    def complete_polygon(self):
        """complete polygon drawing"""
        if len(self.polygon_points) < 3:
            return
            
        # connect last point and first point
        first_x, first_y = self.polygon_points[0]
        last_x, last_y = self.polygon_points[-1]
        
        line = self.canvas.create_line(
            last_x, last_y, first_x, first_y,
            fill=self.get_current_label_color(),
            width=2,
            tags="polygon_line"
        )
        self.polygon_lines.append(line)
        
        # convert to image coordinates
        image_points = []
        for x, y in self.polygon_points:
            img_x = (x - self.image_x) / self.scale
            img_y = (y - self.image_y) / self.scale
            image_points.append((int(img_x), int(img_y)))
        
        # calculate bounding box
        x_coords = [p[0] for p in image_points]
        y_coords = [p[1] for p in image_points]
        bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
        
        # add annotation
        annotation = {
            "bbox": bbox,
            "label": self.label_entry.get().strip(),
            "type": "polygon",
            "points": image_points
        }
        self.annotations.append(annotation)
        self.has_unsaved_mask = True
        
        # initialize polygon drawing state
        self.polygon_points = []
        self.polygon_lines = []
        if self.temp_line:
            self.canvas.delete(self.temp_line)
            self.temp_line = None
        
        # update annotation list
        self.update_annotation_list()
        self.show_toast("Polygon completed!")

    def on_double_click(self, event):
        """complete polygon drawing by double clicking"""
        if self.current_tool == "polygon" and len(self.polygon_points) >= 3:
            self.complete_polygon()

    def download_json(self, format_type="yolo"):
        """download annotation json file"""
        try:
            # Get appropriate annotation path based on format type
            if format_type == "yolo":
                annotation_path = self.yolo_annotation_path
            else:  # coco
                annotation_path = self.coco_annotation_path
                
            if not annotation_path:
                messagebox.showerror("Error", "Annotation path is not set.")
                return
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(annotation_path), exist_ok=True)
            
            # Save annotations
            with open(annotation_path, "w", encoding="utf-8") as f:
                json.dump(self.annotations, f, ensure_ascii=False, indent=2)
            
            self.show_toast(f"Saved as {os.path.basename(annotation_path)}", fg_color=green_color)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {str(e)}")
            return

    def show_toast(self, message, duration=1500, fg_color=None):
        """show toast message"""
        # default color
        default_fg_color = ("#3b82f6", "#2563eb")  # blue
        
        # if toast label is not created, create it
        if self.toast_label is None:
            self.toast_label = ctk.CTkLabel(
                self,
                text="",
                corner_radius=6,  # slightly rounded corners
                text_color="#ffffff"
            )
        
        # if previous toast exists, remove it
        if hasattr(self, '_toast_after') and self._toast_after is not None:
            self.after_cancel(self._toast_after)
            self._toast_after = None
        
        if self.toast_label.winfo_ismapped():
            self.toast_label.place_forget()
        
        # show new toast
        self.toast_label.configure(
            text=message,
            fg_color=fg_color if fg_color is not None else default_fg_color
        )
        
        # calculate toast size and position
        self.toast_label.update()
        toast_width = self.toast_label.winfo_reqwidth()
        toast_height = self.toast_label.winfo_reqheight()
        
        # position at bottom right (padding 20px)
        x = self.winfo_width() - toast_width - 20
        y = self.winfo_height() - toast_height - 20
        
        self.toast_label.place(x=x, y=y)
        self._toast_after = self.after(duration, self._hide_toast)

    def _hide_toast(self):
        """hide toast message"""
        if self.toast_label is not None:
            self.toast_label.place_forget()
        self._toast_after = None

    def activate_drag_mode(self):
        """activate drag mode"""
        self.drag_mode = True
        self.canvas.config(cursor="crosshair")
        # show status message
        self.loading_label.configure(text="Drag mode activated")
        self.loading_label.place(relx=0.5, rely=0.95, anchor="center")
        self.after(1500, lambda: self.loading_label.place_forget())  # hide message after 1.5 seconds

    def display_image(self, pil_img):
        """display image on canvas"""
        if not pil_img:
            return
            
        # get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # ensure canvas has size
        if canvas_width <= 1 or canvas_height <= 1:
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
        
        # image size
        img_width, img_height = pil_img.size
        
        # calculate initial scale (only once)
        if self.initial_scale is None:
            # set target size (800x600)
            target_width = 800
            target_height = 600
            
            # maintain aspect ratio and fit to target size
            width_ratio = target_width / img_width
            height_ratio = target_height / img_height
            self.initial_scale = min(width_ratio, height_ratio)
            self.scale = self.initial_scale
        
        # calculate size with current scale
        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)
        
        # resize image
        resized_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # convert to PhotoImage
        self.photo = ImageTk.PhotoImage(resized_img)
        
        # initialize canvas contents
        self.canvas.delete("all")
        
        # position image in the center of the canvas
        self.image_x = (canvas_width - new_width) // 2
        self.image_y = (canvas_height - new_height) // 2
        
        # create image with specific tag
        self.canvas.create_image(self.image_x, self.image_y, anchor="nw", image=self.photo, tags="main_image")
        
        # redraw all annotations
        self.draw_all_annotations()

    def on_mousewheel(self, event):
        """handle mouse wheel event"""
        # check if mouse is in label list area
        mouse_x = self.winfo_pointerx() - self.winfo_rootx()
        mouse_y = self.winfo_pointery() - self.winfo_rooty()
        
        # check if left panel is visible
        if self.left_panel_visible:
            label_list_bbox = (
                self.left_panel.winfo_x(),
                self.left_panel.winfo_y(),
                self.left_panel.winfo_x() + self.left_panel.winfo_width(),
                self.left_panel.winfo_y() + self.left_panel.winfo_height()
            )
            
            # if in label list area, only scroll
            if (label_list_bbox[0] <= mouse_x <= label_list_bbox[2] and
                label_list_bbox[1] <= mouse_y <= label_list_bbox[3]):
                return
        
        # zoom in/out with Ctrl + wheel
        if event.state & 0x4:  # Ctrl key is pressed
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def setup_floating_nav(self):
        """setup floating navigation"""
        # bottom navigation frame
        self.nav_frame = ctk.CTkFrame(
            self,
            fg_color=panel_color,
            height=40
        )
        self.nav_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        self.nav_frame.grid_propagate(False)
        
        # button container (for centering)
        button_container = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        button_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # left and right buttons and flash button
        prev_img_btn = ctk.CTkButton(
            button_container,
            text="",
            image=self.icons["arrow_left"],
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=gray_color,
            command=self.show_prev_image
        )
        prev_img_btn.pack(side="left", padx=10)
        
        flash_btn = ctk.CTkButton(
            button_container,
            text="",
            image=self.icons["flash"],
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=gray_color,
            command=self.jump_to_next_unannotated
        )
        flash_btn.pack(side="left", padx=10)
        
        next_img_btn = ctk.CTkButton(
            button_container,
            text="",
            image=self.icons["arrow_right"],
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=gray_color,
            command=self.show_next_image
        )
        next_img_btn.pack(side="left", padx=10)

    def update_annotation_list(self):
        """update annotation list"""
        # delete existing list
        for widget in self.annotation_scroll.winfo_children():
            widget.destroy()
            
        # initialize box and polygon counters
        box_counter = 1
        poly_counter = 1
            
        # create item for each annotation
        for i, annotation in enumerate(self.annotations):
            # annotation item frame
            item_frame = ctk.CTkFrame(self.annotation_scroll)
            item_frame.pack(fill="x", padx=5, pady=2)
            
            # apply counter based on annotation type
            if annotation.get("type", "box") == "box":
                type_label = f"box_{box_counter}"
                box_counter += 1
            else:
                type_label = f"poly_{poly_counter}"
                poly_counter += 1
            
            # label button (click to highlight annotation)
            label_btn = ctk.CTkButton(
                item_frame,
                text=type_label,
                command=lambda a=annotation: self.highlight_annotation(a),
                fg_color="transparent",
                text_color=text_color,
                hover_color=gray_color,
                anchor="w"
            )
            label_btn.pack(side="left", fill="x", expand=True, padx=(5, 2))
            
            # delete button
            delete_btn = ctk.CTkButton(
                item_frame,
                text="",
                image=self.icons["eraser"],
                width=30,
                command=lambda a=annotation: self.delete_annotation(a),
                fg_color=icon_color,
                hover_color=icon_color
            )
            delete_btn.pack(side="right", padx=(2, 5))

    def highlight_annotation(self, annotation):
        """highlight selected annotation"""
        # delete all annotations and redraw
        self.canvas.delete("all")
        self.canvas.create_image(self.image_x, self.image_y, anchor="nw", image=self.photo)
        
        # iterate through all annotations and draw
        for i, ann in enumerate(self.annotations):
            bbox = ann["bbox"]
            label = ann["label"]
            box_color = self.label_colors.get(label, "#3b82f6")
            
            # check if current annotation is selected
            is_selected = (ann == annotation)
            
            if ann.get("type", "box") == "box":
                # draw box (convert image coordinates to canvas coordinates)
                canvas_x1 = self.image_x + bbox[0] * self.scale
                canvas_y1 = self.image_y + bbox[1] * self.scale
                canvas_x2 = self.image_x + bbox[2] * self.scale
                canvas_y2 = self.image_y + bbox[3] * self.scale
                
                # create unique tags
                unique_tags = ("annotation", f"id:{i}", f"type:box")
                
                # selected annotation is displayed in red and thick line
                outline_color = "#ff0000" if is_selected else box_color
                line_width = 4 if is_selected else 2
                
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline=outline_color,
                    width=line_width,
                    tags=unique_tags
                )
            else:  # polygon
                # convert polygon points to canvas coordinates
                points = ann.get("points", [])
                canvas_points = []
                for point in points:
                    canvas_x = self.image_x + point[0] * self.scale
                    canvas_y = self.image_y + point[1] * self.scale
                    canvas_points.extend([canvas_x, canvas_y])
                
                if canvas_points:
                    # create unique tags
                    unique_tags = ("annotation", f"id:{i}", f"type:polygon")
                    
                    # selected annotation is displayed in red and thick line
                    outline_color = "#ff0000" if is_selected else box_color
                    line_width = 4 if is_selected else 2
                    
                    self.canvas.create_polygon(
                        canvas_points,
                        outline=outline_color,
                        fill="",
                        width=line_width,
                        tags=unique_tags
                    )
        
        # if selected annotation exists, redraw all annotations after 1 second
        if annotation in self.annotations:
            self.after(1000, self.draw_all_annotations)

    def delete_annotation(self, annotation):
        """delete annotation"""
        
        # remove from annotation list
        self.annotations.remove(annotation)
        
        # update YOLO annotation file
        yolo_path = os.path.join(ANNOTATIONS_DIR, f"{self.task_name}_annotation_yolo.json")
        if os.path.exists(yolo_path):
            try:
                with open(yolo_path, "r", encoding="utf-8") as f:
                    yolo_data = json.load(f)
                
                # update annotation for current image
                if not self.annotations:  # if all annotations are deleted
                    # remove image data completely
                    yolo_data["images"] = [item for item in yolo_data.get("images", [])
                                         if isinstance(item, dict) and 
                                         item.get("image_name") != self.cur_image_name]
                else:
                    # update annotations only
                    for i, item in enumerate(yolo_data.get("images", [])):
                        if isinstance(item, dict) and item.get("image_name") == self.cur_image_name:
                            yolo_data["images"][i]["annotations"] = self.annotations
                            break
                
                # save file
                with open(yolo_path, "w", encoding="utf-8") as f:
                    json.dump(yolo_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.show_toast(f"Failed to update YOLO annotation: {str(e)}", 
                              fg_color=("#ef4444", "#dc2626"))

        # update COCO annotation file
        coco_path = os.path.join(ANNOTATIONS_DIR, f"{self.task_name}_annotation_coco.json")
        if os.path.exists(coco_path):
            try:
                with open(coco_path, "r", encoding="utf-8") as f:
                    coco_data = json.load(f)
                
                # find ID of current image
                image_id = None
                for img in coco_data["images"]:
                    if img["file_name"] == self.cur_image_name:
                        image_id = img["id"]
                        break
                
                if image_id is not None:
                    # remove annotations for current image
                    coco_data["annotations"] = [
                        anno for anno in coco_data["annotations"]
                        if anno["image_id"] != image_id
                    ]
                    
                    if not self.annotations:  # if all annotations are deleted
                        # remove image data from images array
                        coco_data["images"] = [
                            img for img in coco_data["images"]
                            if img["id"] != image_id
                        ]
                    else:
                        # add new annotations
                        for annotation in self.annotations:
                            bbox = annotation["bbox"]
                            label = annotation["label"]
                            label_idx = self.labels.index(label) if label in self.labels else 0
                            
                            x, y = bbox[0], bbox[1]
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]
                            area = width * height
                            
                            annotation_id = len(coco_data["annotations"]) + 1
                            coco_annotation = {
                                "id": annotation_id,
                                "image_id": image_id,
                                "category_id": label_idx + 1,
                                "bbox": [x, y, width, height],
                                "area": area,
                                "iscrowd": 0
                            }
                            
                            # if polygon, add segmentation information
                            if annotation.get("type") == "polygon":
                                points = annotation.get("points", [])
                                segmentation = []
                                for point in points:
                                    segmentation.extend(point)
                                coco_annotation["segmentation"] = [segmentation]
                            else:
                                coco_annotation["segmentation"] = []
                            
                            coco_data["annotations"].append(coco_annotation)
                
                # save file
                with open(coco_path, "w", encoding="utf-8") as f:
                    json.dump(coco_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.show_toast(f"Failed to update COCO annotation: {str(e)}", 
                              fg_color=("#ef4444", "#dc2626"))
        
        # update canvas
        self.canvas.delete("all")
        self.canvas.create_image(self.image_x, self.image_y, anchor="nw", image=self.photo)
        self.draw_all_annotations()
        
        # update annotation list
        self.update_annotation_list()
        
        self.show_toast("Annotation deleted!")