import os
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from dotenv import load_dotenv

# 1. 自动读取同目录下的 .env 文件，把里面的变量加载到系统环境变量中
load_dotenv()

# 2. 从环境变量中安全读取 API_KEY（如果没读到，默认返回 None）
API_KEY = os.getenv("LLM_API_KEY")

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

@app.get("/older")
def older(befor_age: int):
    if befor_age == 120:
        now_age = 0
    else:
        now_age = befor_age + 1
    return{"now_age":now_age}

#1. 定义请求模型（数据契约）Define the request model (data contract)
class lessonRequest(BaseModel):
    topic: str
    grade: str = "三年级"
    duration: int = Field(..., ge=10, le=90)# The class time limit must be between 10 and 90

#2. Defind the response model
class lessonResponse(BaseModel):
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
    #校验通过，正常返回Mock函数
    # 先返回 Mock（假数据），用 req.topic 获取前端传来的课题
    return {
        "title":f"关于{req.topic } 的支教课堂",
        "outline":"1.课堂导入\n2. 核心安全知识讲解\n3. 动手实践与互动",
        "materials":["彩纸","安全剪刀","固体胶"]
    }