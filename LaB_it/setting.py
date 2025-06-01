import os
from PIL import Image
from customtkinter import CTkImage

# foreground color
fg_color = ("#ffffff", "#363434")  # light mode: white, dark mode: dark gray
list_color = ("#f5f5f5", "#18181b")  # light mode: light gray, dark mode: dark gray
list_hover_color = ("#d1d5db", "#3f3f46")  # light mode: light gray, dark mode: dark gray
blue_color = ("#3b82f6", "#2563eb")  # light mode: blue, dark mode: dark blue
red_color = ("#ef4444", "#dc2626")  # light mode: red, dark mode: dark red
green_color = ("#10b981", "#059669")  # light mode: green, dark mode: dark green
gray_color = ("#adadad", "#828282")  # light mode: gray, dark mode: gray
panel_color = ("#f3f4f6", "#6b7480")  # light mode: light gray, dark mode: dark gray
icon_color = ("#ffffff", "#adadad")  # light mode: white, dark mode: gray
text_color = ("#18181b", "#f5f5f5")  # light mode: black, dark mode: white
placeholder_color = ("#64748b", "#9ca3af")  # light mode: gray, dark mode: gray
predefined_color = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD",
    "#D4A5A5", "#9B59B6", "#3498DB", "#E67E22", "#2ECC71",
    "#E74C3C", "#1ABC9C", "#F1C40F", "#8E44AD", "#16A085",
    "#D35400", "#2980B9", "#27AE60", "#C0392B", "#7F8C8D"
]


# directory
TASKS_DIR = os.path.join("LaB_it", "tasks")
ASSETS_DIR = os.path.join("LaB_it", "assets")
ANNOTATIONS_DIR = os.path.join("LaB_it", "annotations")

# icons
sun_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "sun.png")), size=(12, 12))
moon_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "moon.png")), size=(12, 12))
plus_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "plus.png")), size=(15, 15))
upload_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "upload.png")), size=(15, 15))
folder_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "folder.png")), size=(15, 15))
check_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "accept.png")), size=(15, 15))
dots_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "dots.png")), size=(15, 15))
edit_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "edit.png")), size=(15, 15))
delete_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "delete.png")), size=(15, 15))
cursor_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "cursor.png")), size=(15, 15))
box_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "drawing.png")), size=(15, 15))
polygon_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "polygon.png")), size=(15, 15))
erase_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "eraser.png")), size=(15, 15))
zoom_in_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "zoom_in.png")), size=(15, 15))
zoom_out_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "zoom_out.png")), size=(15, 15))
rotate_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "rotate.png")), size=(15, 15))
save_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "save.png")), size=(15, 15))
close_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "close.png")), size=(15, 15))
arrow_left_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "arrow-left.png")), size=(15, 15))
arrow_right_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "arrow-right.png")), size=(15, 15))
arrow_double_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "arrow-double-right.png")), size=(15, 15))
flash_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "flash.png")), size=(15, 15))
download_icon = CTkImage(Image.open(os.path.join(ASSETS_DIR, "download.png")), size=(15, 15))
