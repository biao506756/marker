from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum as PyEnum

class PDFFile(Base):
    __tablename__ = "pdf_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True)
    filepath = Column(String(255))


class TaskStatus(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PDFParseTask(Base):
    __tablename__ = "pdf_parse_tasks"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(String(255), nullable=True)

# 在数据库迁移时需要执行此表的创建