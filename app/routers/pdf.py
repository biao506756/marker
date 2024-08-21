from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.database import get_db
from app.models import PDFFile
from app.schemas import PDFFile as PDFFileSchema, PDFFileCreate
from app.utils.file_utils import save_pdf_file, delete_pdf_file
from typing import List

router = APIRouter(prefix="/pdf", tags=["PDF Files"])

# 上传 PDF 文件（增）
@router.post("/upload", response_model=PDFFileSchema)
def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename
    file_location = save_pdf_file(file, filename)

    pdf_file = PDFFile(filename=filename, filepath=file_location)
    db.add(pdf_file)
    db.commit()
    db.refresh(pdf_file)

    return pdf_file

# 列出所有 PDF 文件（查）
@router.get("/list", response_model=List[PDFFileSchema])
def list_pdfs(db: Session = Depends(get_db)):
    pdf_files = db.query(PDFFile).all()
    return pdf_files

# 下载 PDF 文件（查）
@router.get("/{pdf_id}", response_class=FileResponse)
def download_pdf(pdf_id: int, db: Session = Depends(get_db)):
    pdf_file = db.query(PDFFile).filter(PDFFile.id == pdf_id).first()
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(pdf_file.filepath, media_type='application/pdf', filename=pdf_file.filename)

# 删除 PDF 文件（删）
@router.delete("/{pdf_id}", response_model=PDFFileSchema)
def delete_pdf(pdf_id: int, db: Session = Depends(get_db)):
    pdf_file = db.query(PDFFile).filter(PDFFile.id == pdf_id).first()
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF file not found")

    delete_pdf_file(pdf_file.filepath)
    db.delete(pdf_file)
    db.commit()

    return pdf_file
