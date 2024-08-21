from sqlalchemy import Column, Integer, String
from app.database import Base


class PDFFile(Base):
    __tablename__ = "pdf_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True)
    filepath = Column(String(255))
