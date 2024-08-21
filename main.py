from fastapi import FastAPI
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的请求源（可以指定特定的源或使用 "*" 来允许所有源）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有的HTTP方法
    allow_headers=["*"],  # 允许所有的请求头
)

app.include_router(pdf.router)
