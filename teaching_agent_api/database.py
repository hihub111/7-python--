import sqlite3
import json
from datetime import datetime

DB_NAME = "lessons.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库：包含 safety_json 和 elapsed_seconds 两列"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            grade TEXT NOT NULL,
            content_json TEXT NOT NULL,
            safety_json TEXT NOT NULL,
            elapsed_seconds REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_lesson(topic: str, grade: str, content: dict, safety: dict, elapsed_seconds: float) -> int:
    """存入教案、安全预警报告以及执行耗时"""
    conn = get_connection()
    cursor = conn.cursor()

    content_str = json.dumps(content, ensure_ascii=False)
    safety_str = json.dumps(safety, ensure_ascii=False)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO lessons (topic, grade, content_json, safety_json, elapsed_seconds, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (topic, grade, content_str, safety_str, elapsed_seconds, now_str)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_lessons() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "topic": row["topic"],
            "grade": row["grade"],
            "content": json.loads(row["content_json"]),
            "safety_warning": json.loads(row["safety_json"]),
            "elapsed_seconds": row["elapsed_seconds"],
            "created_at": row["created_at"]
        })
    return result


def get_lesson_by_id(lesson_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "topic": row["topic"],
        "grade": row["grade"],
        "content": json.loads(row["content_json"]),
        "safety_warning": json.loads(row["safety_json"]),
        "elapsed_seconds": row["elapsed_seconds"],
        "created_at": row["created_at"]
    }
