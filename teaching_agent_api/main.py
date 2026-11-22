import os
from dotenv import load_dotenv
from fastapi import FastAPI
import database
from routers import lesson

# 1. 最优先加载 .env 环境变量
load_dotenv()

# 2. 初始化 SQLite 数据库表
database.init_db()

# 3. 创建主应用
app = FastAPI(title="支教 Agent 后端 API")


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
