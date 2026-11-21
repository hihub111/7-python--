import os
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from dotenv import load_dotenv

import database

# 1. 自动读取同目录下的 .env 文件，把里面的变量加载到系统环境变量中
load_dotenv()

# 2. 从环境变量中安全读取 API_KEY（如果没读到，默认返回 None）
API_KEY = os.getenv("LLM_API_KEY")

# 程序启动时，自动初始化数据库表
database.init_db()

app = FastAPI()


@app.get("/health")
def health_check():
    return {"student":"ok",
            # day03新增，测试当前能否安全读到密钥，loob仅返回True或False
            "api_key_loaded": bool(API_KEY)
        }

@app.get("/courses/{course_id}")
def get_course(course_id: int, grade: str = "三年级"):
    return {
        "course_id": course_id,
        "grade": grade
    }

@app.get("/time")
def last_time(age: int,die_age: int = 100):
    return {"end_time":die_age - age }

@app.get("/older")#/{befor_age}
def older(befor_age:int ):
    if befor_age == 120:
        now_age = 0
    else:
        now_age = befor_age + 1
    return{"now_age":now_age,
           "befor_age":befor_age
           }

#1. 定义请求模型（数据契约）Define the request model (data contract)
class lessonRequest(BaseModel):
    topic: str
    grade: str = "三年级"
    duration: int = Field(..., ge=10, le=90)# The class time limit must be between 10 and 90

#2. Defind the response model
class lessonResponse(BaseModel):
    id: int              # 【Day 4 新增】：把数据库生成的记录 ID 返回给前端
    title: str
    outline: str
    materials: list[str]

#3. Write a POST interface
@app.post("/api/lesson/plan",response_model=lessonResponse)
def creat_lesson_plan(req: lessonRequest):
    # day03新增，校验1:去掉首位空格后，检查是否为空字符串
    clean_topic = req.topic.strip()
    if not clean_topic:
        raise HTTPException(status_code=400,detail="课程名不规范,不能为空格")

    # day03新增，校验2:简单的敏感词/危险词拦截
    forbidden_words = ["炸弹","危险品","敏感词"]
    for word in forbidden_words:
        if word in clean_topic:
            raise HTTPException(status_code=400,detail=f"课程包含不允许的词汇：{word}")

    lesson_content = {
        "title":f"关于{clean_topic } 的支教课堂",
        "outline":"1.课堂导入\n2. 核心安全知识讲解\n3. 动手实践与互动",
        "materials":["彩纸","安全剪刀","固体胶"]
    }

    # 【Day 4 新增】：存入 SQLite 数据库，拿到自增 ID
    new_id = database.save_lesson(
        topic=clean_topic,
        grade=req.grade,
        content=lesson_content
    )

    # 把 id 和教案内容合并返回
    return {
        "id": new_id,
        **lesson_content
    }


# 2. 【Day 4 新增】查询所有历史教案列表（GET）
@app.get("/api/lessons")
def list_lessons():
    records = database.get_all_lessons()
    return {
        "total": len(records),
        "items": records
    }


# 3. 【Day 4 新增】根据 ID 查询单条教案（GET + 404 异常拦截）
@app.get("/api/lessons/{lesson_id}")
def get_lesson_detail(lesson_id: int):
    record = database.get_lesson_by_id(lesson_id)
    if record is None:
        # 找不到对应 ID 的记录，抛出标准 404 Not Found 异常！
        raise HTTPException(status_code=404, detail=f"找不到 ID 为 {lesson_id} 的教案记录")
    return record