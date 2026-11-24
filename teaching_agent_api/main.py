import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database
from routers import lesson

# 1. 最优先加载 .env 环境变量
load_dotenv()

# 2. 初始化 SQLite 数据库表
database.init_db()

# 3. 创建主应用
app = FastAPI(title="支教 Agent 后端 API")

# 【Day 7 新增】配置 CORS 跨域资源共享
# 允许运行在其他端口（如 Vue 的 5173 或本地网页）的前端向本后端发请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 开发阶段允许所有来源；上线后可改成具体前端域名
    allow_credentials=True,
    allow_methods=["*"],       # 允许 GET、POST、OPTIONS 等所有请求方式
    allow_headers=["*"],       # 允许所有请求头（如 Content-Type）
)



# 健康检查接口
@app.get("/health")
def health_check():
    api_key = os.getenv("LLM_API_KEY")
    return {
        "status": "ok",
        "api_key_loaded": bool(api_key)
    }


# 4. 挂载教案子路由（把 /api/... 的请求全部分发给 routers/lesson.py 处理）
app.include_router(lesson.router)
