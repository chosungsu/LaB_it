import customtkinter as ctk
from setting import *

class FormatSelectDialog(ctk.CTkToplevel):
    def __init__(self, master, task_name, download_function):
        super().__init__(master)
        self.title("LaB_it-Download")
        self.geometry("500x400")
        self.resizable(False, False)
        self.task_name = task_name
        self.download_function = download_function
        
        # center the window
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        self.geometry(f"500x400+{x}+{y}")
        
        self.configure(fg_color=fg_color)
        
        # main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # title
        title_label = ctk.CTkLabel(
            main_container,
            text="Select format",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))
        
        # button container
        button_container = ctk.CTkFrame(main_container, fg_color="transparent")
        button_container.pack(fill="x", pady=20)
        
        # YOLO button
        yolo_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        yolo_frame.pack(fill="x", pady=(0, 20))
        
        yolo_btn = ctk.CTkButton(
            yolo_frame,
            text="YOLO Format",
            font=ctk.CTkFont(size=15),
            height=50,
            fg_color=blue_color,
            command=lambda: self.download_format("yolo")
        )
        yolo_btn.pack(fill="x")
        
        yolo_desc = ctk.CTkLabel(
            yolo_frame,
            text="Download annotations in YOLO format",
            font=ctk.CTkFont(size=12),
            text_color="#ffffff"
        )
        yolo_desc.pack(pady=(5, 0))
        
        # COCO button
        coco_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        coco_frame.pack(fill="x")
        
        coco_btn = ctk.CTkButton(
            coco_frame,
            text="COCO Format",
            font=ctk.CTkFont(size=15),
            height=50,
            fg_color=green_color,
            command=lambda: self.download_format("coco")
        )
        coco_btn.pack(fill="x")
        
        coco_desc = ctk.CTkLabel(
            coco_frame,
            text="Download annotations in COCO format",
            font=ctk.CTkFont(size=12),
            text_color="#ffffff"
        )
        coco_desc.pack(pady=(5, 0))

    def download_format(self, format_type):
        """
        download annotations in selected format
        """
        self.download_function(format_type)
        self.destroy()