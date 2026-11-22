import os
import json
from openai import AsyncOpenAI
from fastapi import HTTPException

async def generate_lesson_plan(topic: str, grade: str, duration: int) -> dict:
    """异步调用 DeepSeek 大模型，生成结构化 json 教案"""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key or api_key.startswith("sk-test"):
        raise HTTPException(status_code=500,detail = "未配置有效的 DeepSeek API Key，请检查 .env 文件")

    # 1. 创建异步客户端（注意指向 DeepSeek 的官方接口地址）
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    # 2. 编写系统提示词：强约束输出字段，并明确要求 JSON 格式
    system_prompt = """
    你是一名经验丰富的乡村支教课程设计专家。
    请根据用户提供的课题、年级和课时，设计一份适合支教课堂的趣味教案。
    必须严格以 JSON 格式输出，不要包含任何多余的解释文字或 Markdown 标记。
    JSON 必须包含以下三个字段，且字段名和类型必须完全一致：
    1. "title": 字符串，课程标题
    2. "outline": 字符串，教学大纲（请用 \\n 换行分隔各个教学环节，必须是纯字符串，不要用列表）
    3. "materials": 字符串列表，例如 ["彩纸", "安全剪刀", "固体胶"]
    """

    user_prompt = f"课题：{topic}，面向对象：{grade}，总课时：{duration}分钟。"

    try:
        # 3. 发起异步网络请求（遇到 await，CPU 会先去处理其他用户的请求，不死等）
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # 开启 API 级强制 JSON 输出模式
            response_format={"type": "json_object"},
            temperature=0.7
        )

        # 4. 提取大模型返回的文本，并用 json.loads 解析成 Python 字典
        raw_content = response.choices[0].message.content
        lesson_data = json.loads(raw_content)

        # 防御性兜底：万一大模型还是把 outline 返回成了列表，自动用换行符拼成字符串
        if isinstance(lesson_data.get("outline"), list):
            lesson_data["outline"] = "\n".join(lesson_data["outline"])

        return lesson_data

    except Exception as e:
        # 如果网络超时、余额不足或 JSON 解析失败，抛出清晰的 502 网关异常
        raise HTTPException(status_code=502, detail=f"调用 DeepSeek 大模型失败：{str(e)}")