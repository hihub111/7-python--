import time
import json
from fastapi import APIRouter,HTTPException
from fastapi.responses import StreamingResponse     # 【Day 7 新增】流式响应类
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

# ==================== 【Day 7 新增】SSE 流式推送接口 ====================
@router.post("/lesson/plan/stream")
async def creat_lessona_plan_stream(req:LessonRequest):
    # 1. 先执行业务安检（违规依然标准返回 400）
    clean_topic = req.topic.strip()
    if not clean_topic:
        raise HTTPException(status_code=400, detail="课程名不规范，不能为空格")

    forbidden_words = ["炸弹", "危险品", "敏感词"]
    for word in forbidden_words:
        if word in clean_topic:
            raise HTTPException(status_code=400, detail=f"课程包含不允许的词汇：{word}")

    # 2. 定义异步生成器（async def + yield）
    async def event_generator():
        start_time = time.perf_counter()
        try:
            # 进度推送 1
            step1_msg = {"type": "progress", "step": 1, "message": "⏳ 步骤 1/3：正在呼叫 DeepSeek 设计教案与物料清单..."}
            yield f"data: {json.dumps(step1_msg, ensure_ascii=False)}\n\n"

            # 异步等待第一步完成（释放 CPU 给其他用户）
            lesson_content = await generate_lesson_plan(
                topic=clean_topic,
                grade=req.grade,
                duration=req.duration
            )

            # 进度推送 2
            materials_count = len(lesson_content.get("materials", []))
            step2_msg = {
                "type": "progress",
                "step": 2,
                "message": f"✅ 教案已生成（提取到 {materials_count} 项物料），正在进行安全规则扫描与风险评估..."
            }
            yield f"data: {json.dumps(step2_msg, ensure_ascii=False)}\n\n"

            # 异步等待第二步完成
            safety_report = await evaluate_safety_risks(
                topic=clean_topic,
                grade=req.grade,
                materials=lesson_content["materials"]
            )

            # 计入数据库SQL且记时
            elapsed = round(time.perf_counter() - start_time, 2)
            new_id = database.save_lesson(
                topic=clean_topic,
                grade=req.grade,
                content=lesson_content,
                safety=safety_report,
                elapsed_seconds=elapsed
            )

            # 【最终结果推送 3】
            final_payload = {
                "type": "result",
                "step": 3,
                "message": f"🎉 全部完成！总耗时 {elapsed} 秒，已存入数据库（ID: {new_id}）",
                "data": {
                    "id": new_id,
                    **lesson_content,
                    "safety_warning": safety_report,
                    "elapsed_seconds": elapsed
                }
            }
            yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

        except Exception as e:
             # 如果流式传输中途报错，推送一条 error 事件通知前端
            err_msg = {"type": "error", "message": f"❌ 生成过程中发生错误：{str(e)}"}
            yield f"data: {json.dumps(err_msg, ensure_ascii=False)}\n\n"

        # 3. 返回 StreamingResponse，指定 SSE 专属媒体类型
    return StreamingResponse(event_generator(), media_type="text/event-stream")

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