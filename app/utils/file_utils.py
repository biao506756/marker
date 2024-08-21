import os
from fastapi import HTTPException

UPLOAD_DIR = "uploads"

def save_pdf_file(upload_file, filename):
    file_location = os.path.join('uploads', filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    with open(file_location, "wb+") as file_object:
        file_object.write(upload_file.file.read())  # 确保你正在从 UploadFile 读取数据

    return file_location

def delete_pdf_file(filepath):
    try:
        os.remove(filepath)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
