import time
from fastapi import APIRouter,HTTPException
from schemas import LessonRequest,LessonResponse
from services.llm import generate_lesson_plan
from services.safety import evaluate_safety_risks
import database

# 创建子路由，统一加上 "/api" 前缀，保持和 Day 4 完全一致的接口网址！
router = APIRouter(prefix="/api",tags=["教案生成与管理"])

# 1. 创建并保存教案（异步接口！）
@router.post("/lesson/plan",response_model=LessonResponse)
async def create_lesson_plan(req: LessonRequest):
    clean_topic = req.topic.strip()
    if not clean_topic:
        raise HTTPException(status_code=400,detail="课程名不规范，不能为空格")
    forbidden_words = ["炸弹", "危险品", "敏感词"]
    for word in forbidden_words:
        if word in clean_topic:
            raise HTTPException(status_code=400, detail=f"课程包含不允许的词汇：{word}")

    #按下高性能秒表
    start_time = time.perf_counter()

    # 2. 【工作流第一步】：异步调用 DeepSeek 生成教案与物料列表
    lesson_content = await generate_lesson_plan(
        topic=clean_topic,
        grade=req.grade,
        duration=req.duration
    )

    # 3. 【工作流第二步（链式传递）】：把第一步生成的 materials 交给安全预警模块
    safety_report = await evaluate_safety_risks(
        topic=clean_topic,
        grade=req.grade,
        materials=lesson_content["materials"]
    )

    # 4. 停止秒表，计算全链路真实耗时（保留 2 位小数）
    elapsed = round(time.perf_counter() - start_time, 2)

    #存入 SQLite 数据库，拿到自增id
    new_id = database.save_lesson(
        topic=clean_topic,
        grade=req.grade,
        content=lesson_content,
        safety=safety_report,
        elapsed_seconds=elapsed
    )

    return {
        "id": new_id,
        **lesson_content,
        "safety_warning": safety_report,
        "elapsed_seconds": elapsed
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