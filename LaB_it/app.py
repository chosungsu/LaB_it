import customtkinter as ctk
import os
from CTkMenuBar import *
from .dialog.taskmanagerdialog import TaskManagerDialog
from .setting import *

# create necessary directories
for dir_path in [TASKS_DIR, ANNOTATIONS_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

class LaB_itApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # hide main window
        self.withdraw()

        TaskManagerDialog(self)

def launch_app():
    app = LaB_itApp()
    app.mainloop()

if __name__ == "__main__":
    launch_app()
