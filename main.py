import logging

from app.database import engine, Base
from app.routers import pdf
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers.parse import initialize_models, process_pdf_file  # 从 parse 模块导入函数
from marker.logger import configure_logging  # 导入日志配置函数
from marker.models import load_all_models  # 用于加载模型
# 全局变量用于存储加载的模型列表
model_list = None
# 初始化日志配置
configure_logging()
logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_models()  # 加载所有模型
    yield  # 在这里可以执行一些应用启动时的操作，比如资源加载、模型初始化等
# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI()
# 允许的源名单，这里示例允许所有源
origins = [
    "http://192.168.10.132:8080",  # 允许前端所在的地址
    "http://localhost:8080"  # 如果你还在本地测试，也可以加入localhost的端口
]

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 注册路由
app.include_router(pdf.router)

# 在代码中启动Uvicorn服务器
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
