from pydantic import BaseModel, Field


# 请求模型：规定前端传过来的 JSON 必须长什么样
class LessonRequest(BaseModel):
    topic: str
    grade: str = "三年级"
    duration: int = Field(..., ge=10, le=90)


# 响应模型：规定后端返回给前端的 JSON 长什么样
class LessonResponse(BaseModel):
    id: int
    title: str
    outline: str
    materials: list[str]
