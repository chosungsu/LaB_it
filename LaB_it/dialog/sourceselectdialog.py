import customtkinter as ctk
from ..setting import *

class SourceSelectDialog(ctk.CTkToplevel):
    def __init__(self, master, task_name, on_source_selected):
        super().__init__(master)
        self.title("LaB_it-Select")
        self.geometry("500x400")
        self.resizable(False, False)
        
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
            text="Select path",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))
        
        # button container
        button_container = ctk.CTkFrame(main_container, fg_color="transparent")
        button_container.pack(fill="x", pady=20)
        
        # Drive button
        drive_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        drive_frame.pack(fill="x", pady=(0, 20))
        
        drive_btn = ctk.CTkButton(
            drive_frame,
            text="Google Drive",
            font=ctk.CTkFont(size=15),
            height=50,
            fg_color=blue_color,
            hover_color=blue_color,
            command=lambda: self.on_select("drive")
        )
        drive_btn.pack(fill="x")
        
        drive_desc = ctk.CTkLabel(
            drive_frame,
            text="Access and label images from Google Drive",
            font=ctk.CTkFont(size=12),
            text_color="#ffffff"
        )
        drive_desc.pack(pady=(5, 0))
        
        # Local button
        local_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        local_frame.pack(fill="x")
        
        local_btn = ctk.CTkButton(
            local_frame,
            text="Local Storage",
            font=ctk.CTkFont(size=15),
            height=50,
            fg_color=green_color,
            hover_color=green_color,
            command=lambda: self.on_select("local")
        )
        local_btn.pack(fill="x")
        
        local_desc = ctk.CTkLabel(
            local_frame,
            text="Label images from your local storage",
            font=ctk.CTkFont(size=12),
            text_color="#ffffff"
        )
        local_desc.pack(pady=(5, 0))
        
        self.task_name = task_name
        self.on_source_selected = on_source_selected

    def on_select(self, source_type):
        self.destroy()
        self.on_source_selected(self.task_name, source_type)