import customtkinter as ctk
from setting import *
from CTkMenuBar import *
import os
import json
from tkinter import messagebox

class TaskManagerDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("LaB_it-Select Task")
        self.geometry("600x500")
        self.resizable(False, False)
        self.selected_task = None
        self.editing_task = None
        self.edit_frame = None

        # center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 500
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # appearance mode state
        self.appearance_mode = ctk.get_appearance_mode()

        # load icon images
        self.sun_icon = sun_icon
        self.moon_icon = moon_icon
        self.check_icon = check_icon
        self.plus_icon = plus_icon
        self.dots_icon = dots_icon
        self.edit_icon = edit_icon
        self.delete_icon = delete_icon

        # grid layout
        self.grid_columnconfigure(0, weight=1, minsize=200)  # left(list)
        self.grid_columnconfigure(1, weight=2, minsize=350)  # right(settings)
        self.grid_rowconfigure(1, weight=1)

        self.configure(fg_color=fg_color)

        # top bar (title + dark/light toggle)
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

        # left(list)
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nswe", padx=(20, 10), pady=10)
        left_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(left_frame, text="Tasks", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.task_listbox = ctk.CTkScrollableFrame(left_frame, height=350, fg_color="transparent")
        self.task_listbox.grid(row=1, column=0, sticky="nswe")
        self.task_buttons = []
        self.refresh_task_list()

        # right(settings)
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=1, sticky="nswe", padx=(10, 20), pady=10)
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # New Task section
        ctk.CTkLabel(self.right_frame, text="Create a Task", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.new_task_entry = ctk.CTkEntry(self.right_frame, placeholder_text="ex: product_labeling", takefocus=False)
        self.new_task_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.new_task_entry.bind("<Return>", lambda event: self.create_task())
        ctk.CTkButton(
            self.right_frame, 
            text="Create", 
            image=self.plus_icon, 
            compound="left", 
            command=self.create_task, 
            fg_color=green_color, 
            text_color="#ffffff",
            hover_color=green_color
        ).grid(row=2, column=0, sticky="ew", pady=(0, 15))

        # Load Task section (initially hidden)
        self.load_section = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.load_section.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.load_section.grid_remove()  # initally hidden
        
        ctk.CTkLabel(self.load_section, text="Selected Task", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.selected_task_label = ctk.CTkLabel(self.load_section, text="", font=ctk.CTkFont(size=13))
        self.selected_task_label.pack(anchor="w", pady=(0, 10))
        
        self.load_button = ctk.CTkButton(
            self.load_section,
            text="Load",
            image=self.check_icon,
            compound="left",
            command=self.load_task,
            fg_color=blue_color,
            text_color="#ffffff",
            hover_color=blue_color
        )
        self.load_button.pack(fill="x")

    def refresh_task_list(self):
        for widget in self.task_listbox.winfo_children():
            widget.destroy()
        self.task_buttons.clear()
        
        for f in os.listdir(TASKS_DIR):
            if f.endswith(".json"):
                # task frame
                task_frame = ctk.CTkFrame(self.task_listbox, fg_color="transparent")
                task_frame.pack(fill="x", pady=4, padx=5)
                task_frame.grid_columnconfigure(0, weight=1)
                
                # task button
                btn = ctk.CTkButton(
                    task_frame,
                    text=f[:-5],
                    width=300,
                    fg_color=list_color,
                    hover_color=list_hover_color,
                    text_color=text_color
                )
                btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
                btn.bind("<Button-1>", lambda event, name=f: self.on_task_button_click(event, name))
                btn.bind("<Double-Button-1>", lambda event, name=f: self.on_task_button_double_click(event, name))
                
                # menu button
                menu_btn = ctk.CTkButton(
                    task_frame,
                    text="",
                    image=self.dots_icon,
                    width=30,
                    fg_color=icon_color,
                    hover_color=icon_color
                )
                menu_btn.grid(row=0, column=1, padx=(0, 5))
                menu_btn.bind("<Button-1>", lambda event, name=f: self.show_task_menu(name, None, 0, 0))
                
                self.task_buttons.append(btn)

    def show_task_menu(self, task_name, menu_btn, x, y):
        # modal window
        modal = ctk.CTkToplevel(self)
        modal.title("LaB_it-Task menu")
        modal.geometry("300x150")
        modal.resizable(False, False)
        
        # modal to current window
        self.update_idletasks()
        modal.update_idletasks()
        
        # current window position and size
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        
        # modal window size
        modal_width = 300
        modal_height = 150
        
        # modal window position calculation (TaskManager window center)
        x = parent_x + (parent_width - modal_width) // 2
        y = parent_y + (parent_height - modal_height) // 2
        
        modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
        modal.configure(fg_color=fg_color)
        
        # modal to top
        modal.transient(self)
        modal.grab_set()
        
        # modal content
        content_frame = ctk.CTkFrame(modal, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=25, pady=10)
        
        # button frame
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        
        # Edit button
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="Edit",
            image=self.edit_icon,
            compound="left",
            command=lambda: [modal.destroy(), self.show_edit_modal(task_name)],
            fg_color=blue_color,
            text_color="#ffffff",
            hover_color=blue_color,
            anchor="w",
            height=45
        )
        edit_btn.pack(fill="x", pady=(0, 15))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            image=self.delete_icon,
            compound="left",
            command=lambda: [modal.destroy(), self.delete_task(task_name)],
            fg_color=red_color,
            text_color="#ffffff",
            hover_color=red_color,
            anchor="w",
            height=45
        )
        delete_btn.pack(fill="x", pady=(0, 15))

    def show_edit_modal(self, task_name):
        # edit modal window
        modal = ctk.CTkToplevel(self)
        modal.title("LaB_it-Edit Task")
        modal.geometry("400x200")
        modal.resizable(False, False)
        
        # modal to current window
        self.update_idletasks()
        modal.update_idletasks()
        
        # current window position and size
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        
        # modal window size
        modal_width = 400
        modal_height = 200
        
        # modal window position calculation
        x = parent_x + (parent_width - modal_width) // 2
        y = parent_y + (parent_height - modal_height) // 2
        
        modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
        modal.configure(fg_color=fg_color)
        
        # modal to top
        modal.transient(self)
        modal.grab_set()
        
        # modal content
        content_frame = ctk.CTkFrame(modal, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=25, pady=10)
        
        # title
        title_label = ctk.CTkLabel(
            content_frame, 
            text="Edit Task Name", 
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 5))
        
        # input field
        entry_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        entry_frame.pack(fill="x", pady=(0, 20))
        
        edit_entry = ctk.CTkEntry(
            entry_frame, 
            placeholder_text="Enter new task name",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=list_color,
            border_color=list_color,
            text_color=text_color
        )
        edit_entry.insert(0, task_name[:-5])
        edit_entry.pack(fill="x")
        
        # button frame
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=modal.destroy,
            fg_color=gray_color,
            text_color="#ffffff",
            hover_color=gray_color,
            width=120,
            height=40
        )
        cancel_btn.pack(side="left", padx=(0, 5))
        
        # save button
        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            command=lambda: [
                self.save_task_edit(task_name, edit_entry.get()),
                modal.destroy()
            ],
            fg_color=green_color,
            text_color="#ffffff",
            hover_color=green_color,
            width=120,
            height=40
        )
        save_btn.pack(side="left")

    def save_task_edit(self, old_name, new_name):
        if not new_name:
            messagebox.showerror("Error", "Please enter a task name.")
            return
            
        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror("Error", "Task name cannot be empty.")
            return
            
        old_path = os.path.join(TASKS_DIR, old_name)
        new_path = os.path.join(TASKS_DIR, f"{new_name}.json")
        
        # multiple annotation file format paths
        annotation_formats = [
            ("yolo_drive", "_annotation_yolo_drive.json"),
            ("coco_drive", "_annotation_coco_drive.json"),
            ("yolo_local", "_annotation_yolo_local.json"),
            ("coco_local", "_annotation_coco_local.json")
        ]
        
        old_annotation_paths = []
        new_annotation_paths = []
        
        # create file paths for each format
        for _, suffix in annotation_formats:
            old_annotation_paths.append(os.path.join(ANNOTATIONS_DIR, f"{old_name[:-5]}{suffix}"))
            new_annotation_paths.append(os.path.join(ANNOTATIONS_DIR, f"{new_name}{suffix}"))
        
        if old_name == f"{new_name}.json":
            return
        
        try:
            if os.path.exists(new_path):
                messagebox.showerror("Error", "This task name already exists.")
                return
            
            # rename tasks file
            os.rename(old_path, new_path)

            # rename annotation files if they exist
            for old_path, new_path in zip(old_annotation_paths, new_annotation_paths):
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)

            # update selected task label
            if self.selected_task == old_name:
                self.selected_task = f"{new_name}.json"
                self.selected_task_label.configure(text=new_name)
            self.refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename task: {str(e)}")

    def delete_task(self, task_name):
        try:
            os.remove(os.path.join(TASKS_DIR, task_name))
            self.refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {str(e)}")

    def toggle_mode(self):
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        is_dark = new_mode == "Dark"
        
        self.mode_btn.configure(
            image=self.sun_icon if is_dark else self.moon_icon,
            fg_color=icon_color
        )
        
        self.configure(fg_color=fg_color)
        self.refresh_task_list()

    def on_task_button_click(self, event, name):
        # if the same task is clicked again, select it
        if self.selected_task == name:
            self.selected_task = None
            for btn in self.task_buttons:
                btn.configure(fg_color=list_color)
            self.load_section.grid_remove()
            return
            
        # previous selection
        for btn in self.task_buttons:
            btn.configure(fg_color=list_color)
            
        # find current button and select it
        for btn in self.task_buttons:
            if btn.cget("text") == name[:-5]:  # exclude .json
                btn.configure(fg_color=blue_color)
                self.selected_task = name
                # show Load section and update
                self.selected_task_label.configure(text=name[:-5])
                self.load_section.grid()
                break
        else:
            self.selected_task = None
            self.load_section.grid_remove()

    def on_task_button_double_click(self, event, name):
        self.selected_task = None
        for btn in self.task_buttons:
            btn.configure(fg_color=list_color)
        self.load_section.grid_remove()

    def create_task(self):
        name = self.new_task_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a task name.")
            return
        path = os.path.join(TASKS_DIR, f"{name}.json")
        if os.path.exists(path):
            messagebox.showerror("Error", "This task name already exists.")
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        self.destroy()

    def load_task(self):
        """load task"""
        from dialog.sourceselectdialog import SourceSelectDialog
        if self.selected_task:
            # hide main window
            self.withdraw()
            
            def on_source_selected(task_name, source_type):
                from dialog.settingdialog import SetupDialog
                self.withdraw()  # hide TaskManager window
                def on_setup_done(folder_id, labels):
                    self.destroy()  # TaskManager completely close
                def on_back_to_main():
                    self.deiconify()  # TaskManager show again
                SetupDialog(self.master, task_name, on_setup_done, source_type, on_back_to_main)
            SourceSelectDialog(self, self.selected_task[:-5], on_source_selected)
