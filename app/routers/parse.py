from datetime import datetime
from fastapi import FastAPI, APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os
import base64
import time
import logging
import asyncio
import concurrent.futures
from marker.parse import parse_single_pdf  # 你可能已经有的函数
from marker.logger import configure_logging  # 用于配置日志
from marker.models import load_all_models  # 用于加载模型
from app.models import PDFFile, PDFParseTask, TaskStatus
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/parse", tags=["PDF Files"])

# 初始化日志配置
configure_logging()
logger = logging.getLogger(__name__)

def initialize_models():
    """
    初始化OCR模型。

    该函数加载所有需要的OCR模型并存储在全局变量中，供后续使用。
    """
    global model_list
    logger.debug("加载所有OCR模型")
    model_list = load_all_models()

@router.post("/convert")
async def convert_pdf_to_markdown(pdf_file: UploadFile):
    """
    将单个PDF文件转换为Markdown。

    参数:
    pdf_file (UploadFile): 上传的PDF文件。

    返回:
    FileResponse: 返回生成的Markdown文件的下载链接。
    """
    logger.debug(f"收到文件: {pdf_file.filename}")
    file = await pdf_file.read()  # 读取上传的文件内容
    response = process_pdf_file(file, pdf_file.filename)  # 处理PDF文件

    # 生成Markdown文件
    markdown_filename = f"{os.path.splitext(pdf_file.filename)[0]}.md"
    with open(markdown_filename, 'w', encoding='utf-8') as md_file:
        md_file.write(response['markdown'])

    logger.debug(f"Markdown 文件已生成: {markdown_filename}")

    # 返回文件响应
    return FileResponse(markdown_filename, media_type='text/markdown', filename=markdown_filename)

@router.post("/batch_convert")
async def convert_pdfs_to_markdown(pdf_file: List[UploadFile] = File(...)):
    """
    批量将多个PDF文件转换为Markdown。

    参数:
    pdf_file (List[UploadFile]): 上传的多个PDF文件。

    返回:
    List[dict]: 包含每个PDF文件转换结果的字典列表。
    """
    logger.debug(f"收到 {len(pdf_file)} 个文件用于批量转换")

    async def process_files(files):
        """
        异步处理多个PDF文件的转换。

        参数:
        files (List[UploadFile]): 要处理的PDF文件列表。

        返回:
        List[dict]: 每个文件的处理结果。
        """
        loop = asyncio.get_event_loop()  # 获取事件循环
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            coroutines = [
                loop.run_in_executor(pool, process_pdf_file, await file.read(), file.filename)
                for file in files
            ]
            return await asyncio.gather(*coroutines)  # 异步并发地处理文件

    responses = await process_files(pdf_file)  # 调用异步处理函数
    return responses

@router.post("/parse/{pdf_id}", response_model=dict)
async def parse_pdf_by_id(pdf_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    根据PDF文件ID解析PDF文件。

    参数:
    pdf_id (int): 要解析的PDF文件ID。
    background_tasks (BackgroundTasks): FastAPI的后台任务实例。
    db (Session): 数据库会话。

    返回:
    dict: 包含任务ID、状态和消息的字典。
    """
    pdf_file = db.query(PDFFile).filter(PDFFile.id == pdf_id).first()
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF file not found")

    pdf_path = pdf_file.filepath
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    # 创建解析任务
    parse_task = PDFParseTask(filename=pdf_file.filename, status=TaskStatus.PENDING)
    db.add(parse_task)
    db.commit()
    db.refresh(parse_task)

    # 添加到后台任务中
    background_tasks.add_task(parse_pdf_task, parse_task.id, pdf_path, db)

    return {
        "task_id": parse_task.id,
        "status": parse_task.status,
        "message": "Task created, processing in background."
    }

@router.get("/task/{task_id}", response_model=dict)
def get_task_status(task_id: int, db: Session = Depends(get_db)):
    """
    获取PDF解析任务的状态。

    参数:
    task_id (int): 任务ID。
    db (Session): 数据库会话。

    返回:
    dict: 包含任务ID、文件名、状态、创建时间、完成时间和结果的字典。
    """
    task = db.query(PDFParseTask).filter(PDFParseTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "filename": task.filename,
        "status": task.status.value,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "result": task.result
    }

def parse_pdf_task(task_id: int, pdf_path: str, db: Session):
    """
    后台任务：解析指定ID的PDF文件。

    参数:
    task_id (int): 任务ID。
    pdf_path (str): PDF文件的路径。
    db (Session): 数据库会话。
    """
    task = db.query(PDFParseTask).filter(PDFParseTask.id == task_id).first()
    if not task:
        logger.error(f"Task {task_id} not found in database.")
        return

    task.status = TaskStatus.IN_PROGRESS
    db.commit()

    try:
        with open(pdf_path, "rb") as f:
            file_content = f.read()

        logger.debug(f"开始解析文件: {task.filename}")
        response = process_pdf_file(file_content, task.filename)

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = "File parsed successfully."
        db.commit()

        logger.info(f"Task {task_id} completed successfully.")
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.result = f"Failed to parse file: {str(e)}"
        db.commit()
        logger.error(f"Task {task_id} failed: {str(e)}")

def parse_pdf_and_return_markdown(pdf_file: bytes, extract_images: bool):
    """
    解析PDF并提取文本和图像。

    参数:
    pdf_file (bytes): PDF文件的内容。
    extract_images (bool): 是否提取图像。

    返回:
    tuple: 包含完整文本、元数据和图像数据（如果提取）的元组。
    """
    logger.debug("解析PDF文件")
    full_text, images, out_meta = parse_single_pdf(pdf_file, model_list)  # 调用解析函数
    logger.debug(f"提取的图像: {list(images.keys())}")
    image_data = {}
    if extract_images:
        for i, (filename, image) in enumerate(images.items()):
            logger.debug(f"处理图像 {filename}")

            # 将图像保存为PNG格式
            image.save(filename, "PNG")

            # 将保存的图像文件读取为字节
            with open(filename, "rb") as f:
                image_bytes = f.read()

            # 将图像转换为Base64格式
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            image_data[f'{filename}'] = image_base64

            # 删除临时图像文件
            os.remove(filename)

    return full_text, out_meta, image_data

def process_pdf_file(file_content: bytes, filename: str):
    """
    处理单个PDF文件。

    参数:
    file_content (bytes): PDF文件的内容。
    filename (str): PDF文件的名称。

    返回:
    dict: 包含文件名、Markdown文本、元数据、图像数据、状态和处理时间的字典。
    """
    entry_time = time.time()
    logger.info(f"{filename} 的进入时间: {entry_time}")
    markdown_text, metadata, image_data = parse_pdf_and_return_markdown(file_content, extract_images=True)
    completion_time = time.time()
    logger.info(f"{filename} 的模型处理完成时间: {completion_time}")
    time_difference = completion_time - entry_time  # 计算处理时间
    return {
        "filename": filename,
        "markdown": markdown_text,
        "metadata": metadata,
        "images": image_data,
        "status": "ok",
        "time": time_difference
    }
