import os
import json
from openai import AsyncOpenAI
from fastapi import HTTPException

# 1. 硬编码确定性高危物品规则字典（第一道防线：100% 确定，绝不依赖大模型概率）
HIGH_RISK_RULES = {
    "锐物":["剪刀", "美工刀", "刻刀", "针", "图钉", "铁丝"],
    "电源电路":["电池", "导线", "电线", "马达", "电机", "插座", "电源"],
    "高温":["打火机", "火柴", "酒精灯", "蜡烛", "热水", "开水", "电烙铁"],
    "化学物品":["酒精", "双氧水", "白醋", "小苏打", "胶水", "502"]
}

async def evaluate_safety_risks(topic: str, grade: str, materials: list[str]) -> dict:
    """链式第二步：先用确定性规则扫描物料，再调用 DeepSeek 生成课堂防范建议"""
    matched_items = []
    rule_alerts = []

    # 第一道防线，python确定性规则扫描
    for item in materials:
        for category,keywords in HIGH_RISK_RULES.items():
            for kw in keywords:
                if kw in item:
                    matched_items.append(f"{item}（{category}）")
                    rule_alerts.append(f"【强制红警】检测到{category}物品“{item}”，严禁学生脱离视线单独操作！")
                    break

    # 去重（保持原有顺序）
    matched_items = list(dict.fromkeys(matched_items))
    rule_alerts = list(dict.fromkeys(rule_alerts))

    # 只要命中任何一条规则，代码层强制锁定安全级为 HIGH
    risk_level = "HIGH" if matched_items else "LOW"

    # 第二道防线，交给 DeepSeek 异步处理
    api_key = os.getenv("LLM_API_KEY")
    if not api_key or api_key.startswith("sk-test"):
        raise HTTPException(status_code=500,detail="未正确配置deepseek key")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    system_prompt = """
    你是一名严谨的中小学支教安全督导员。
    请根据课程名称、学生年级、物料清单以及系统已检测出的高危物品，给出具体、可落地的课堂安全防范操作建议。
    必须严格以 JSON 格式输出，且只包含一个字段：
    {
        "ai_suggestions": "具体的防范建议纯文本（用 \\n 分点列出，不要用列表）"
    }
    """

    user_prompt = (
        f"课题：{topic}，年级：{grade}。\n"
        f"课堂物料清单：{materials}。\n"
        f"系统规则已命中的高危物品：{matched_items if matched_items else '无明显高危物品'}。"
    )

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # 安全建议要求严谨稳定，调低随机性
        )

        raw_content = response.choices[0].message.content
        ai_data = json.loads(raw_content, strict=False)
        suggestions = ai_data.get("ai_suggestions", "请老师在课前检查所有教具安全性，全程巡视指导。")

        # 防御兜底：万一模型返回了列表，自动拼成字符串
        if isinstance(suggestions, list):
            suggestions = "\n".join(suggestions)

    except Exception as e:
        # 工程亮点：即使大模型网络超时报错，我们的确定性规则依然能成功兜底返回！
        suggestions = f"（AI 建议生成暂不可用：{str(e)}）请严格遵照上方红色预警规范执行课堂安全管理。"

    return {
        "risk_level": risk_level,
        "matched_items": matched_items,
        "rule_alerts": rule_alerts,
        "ai_suggestions": suggestions
    }