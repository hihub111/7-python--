from fastapi import FastAPI
from pydantic import BaseModel,Field

app = FastAPI()

@app.get("/health")
def health_check():
    return {"student":"ok"}

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
@app.post("/api/lisson/plan",response_model=lessonResponse)
def creat_lesson_plan(req: lessonRequest):
    # 先返回 Mock（假数据），用 req.topic 获取前端传来的课题
    return {
        "title":f"关于{req.topic } 的支教课堂",
        "outline":"1.课堂导入\n2. 核心安全知识讲解\n3. 动手实践与互动",
        "materials":["彩纸","安全剪刀","固体胶"]
    }