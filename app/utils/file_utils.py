import os
from fastapi import HTTPException

UPLOAD_DIR = "uploads"

def save_pdf_file(file, filename):
    file_location = os.path.join(UPLOAD_DIR, filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return file_location

def delete_pdf_file(filepath):
    try:
        os.remove(filepath)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
