from pydantic import BaseModel, Field


# 请求模型：规定前端传过来的 JSON 必须长什么样
class LessonRequest(BaseModel):
    topic: str
    grade: str = "三年级"
    duration: int = Field(..., ge=10, le=90)

# day06 新增，增加安全预警的数据契约
class SafetyWarning(BaseModel):
    risk_level: str             # "HIGH"（高危红警）或 "LOW"（常规低风险）
    matched_items: list[str]    # 规则引擎命中的高危物品及类别
    rule_alerts: list[str]      # 硬编码规则强制触发的警告语
    ai_suggestions: str          # DeepSeek 生成的针对性课堂防范建议



# 响应模型：规定后端返回给前端的 JSON 长什么样
class LessonResponse(BaseModel):
    id: int
    title: str
    outline: str
    materials: list[str]
    safety_warning: SafetyWarning   # 【Day 6 新增】嵌套安全报告
    elapsed_seconds: float          # 【Day 6 新增】全链路执行耗时（秒）
