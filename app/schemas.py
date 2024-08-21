from pydantic import BaseModel

class PDFFileBase(BaseModel):
    filename: str

class PDFFileCreate(PDFFileBase):
    pass

class PDFFile(PDFFileBase):
    id: int
    filepath: str

    class Config:
        orm_mode = True
