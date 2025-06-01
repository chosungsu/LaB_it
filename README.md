# LaB_it (Labeling Tool)

[English](README.md) | [한국어](README.ko.md)

A modern labeling tool built with CustomTkinter, providing an intuitive GUI interface for easy image segmentation and analysis.

## Key Features

- Intuitive GUI Interface
- Image Upload and Management
- Click-based Object Segmentation
- Segmentation Result Management
- Google Drive Integration

## Installation

1. Create and Activate Virtual Environment
```bash
python -m venv .venv
# Windows
source .venv/Scripts/activate
# Linux/Mac
source .venv/bin/activate
```

2. Install Required Packages
```bash
pip install .
```

3. Set up Google Cloud Service Account
   1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   2. Create a new project or select an existing one
   3. Navigate to 'IAM & Admin' > 'Service Accounts' in the left menu
   4. Click 'Create Service Account'
   5. Enter service account name (e.g., lab-it-service)
   6. Click 'Create and Continue'
   7. Select role: Grant 'Editor' permission
   8. Click 'Done'
   9. Click on the created service account
   10. Select 'Keys' tab > 'Add Key' > 'Create New Key' > Select JSON
   11. Save the downloaded JSON file as `service_account.json` in the project root folder

4. Run the Application
```bash
python -m LaB_it
```

## Project Structure
```
LaB_it/
├── LaB_it/
│   ├── annotations/     # Segmentation results
│   ├── assets/         # Images and resources
│   ├── dialog/         # UI modules
│   ├── tasks/          # Task-related modules
│   ├── __init__.py
│   ├── __main__.py     # Main entry point
│   ├── setting.py      # Icons, paths, colors configuration
│   └── app.py          # Main logic
├── .gitignore
├── README.md
├── requirements.txt    # Required packages
└── setup.py           # Installation configuration
```

## Required Packages
- torch & torchvision: Deep learning framework
- customtkinter: Modern GUI interface
- opencv-python: Image processing
- google-api-python-client: Google Drive integration

## References
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 