from fastapi import APIRouter,HTTPException
from schemas import LessonRequest,LessonResponse
from services.llm import generate_lesson_plan
import database

# 创建子路由，统一加上 "/api" 前缀，保持和 Day 4 完全一致的接口网址！
router = APIRouter(prefix="/api",tags=["教案生成与管理"])

# 1. 创建并保存教案（异步接口！）
@router.post("/lesson/plan",response_model=LessonResponse)
async def create_lesson_plan(req: LessonRequest):
    clean_topic = req.topic.strip()
    if not clean_topic:
        raise HTTPException(status_code=400,detail="课程名不规范，不能为空格")
    
    # 【Day 5 核心升级】：替换掉原来的假数据，异步等待 DeepSeek 生成真实教案！
    lesson_content = await generate_lesson_plan(
        topic=clean_topic,
        grade=req.grade,
        duration=req.duration
    )

    #存入 SQLite 数据库，拿到自增id
    new_id = database.save_lesson(
        topic=clean_topic,
        grade=req.grade,
        content=lesson_content
    )

    return {
        "id": new_id,
        **lesson_content
    }

    # 2. 查询所有历史教案列表
@router.get("/lessons")
def list_lessons():
    records = database.get_all_lessons()
    return {
        "total": len(records),
        "items": records
    }


# 3. 根据 ID 查询单条教案
@router.get("/lessons/{lesson_id}")
def get_lesson_detail(lesson_id: int):
    record = database.get_lesson_by_id(lesson_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"找不到 ID 为 {lesson_id} 的教案记录")
    return record