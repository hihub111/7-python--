import sqlite3
import json
from datetime import datetime

#数据库文件名（运行后自动在当前目录生成这个文件）
DB_NAME = "lessons.db"

def get_connection():
    #获取数据库连接（每次操作独立建立连接，避免 FastAPI 多线程报错）
    conn = sqlite3.connect(DB_NAME)
    #关键配置：让查询结果可以通过列表名取值（像字典一样），而不是难懂的元组（1，‘科学’，...）
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    #初始化数据库：如果 lessons 表不存在，就自动创建它
    conn = get_connection()
    cursor = conn.cursor()
    #执行SQL建表语句，严格对应我们的五个字段
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            grade TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_lesson(topic: str,grade: str,content: dict)->int:
    """将一条教案存入数据库，并返回系统自动生成的自增 id"""
    conn = get_connection()
    cursor = conn.cursor()

    # SQLite 不能直接存 Python 字典/列表，必须用 json.dumps 转成 JSON 字符串
    content_str = json.dumps(content,ensure_ascii=False)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #注意：用 ? 占位符传参，这是防止“SQL 注入攻击”的标准安全写法！
    cursor.execute(
        "INSERT INTO lessons (topic, grade, content_json, created_at) VALUES (?,?,?,?)",
        (topic ,grade, content_str, now_str)
    )
    conn.commit()
    #拿到刚刚插入这条数据的自增 ID
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_lessons() -> list[dict]:
    """查询所有历史教案记录（按时间倒序，最新的在最前面）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id":row["id"],
            "topic":row["topic"],
            "grade":row["grade"],
            #取出来时，用json.loads 把字符串还原回 python 字典
            "content":json.loads(row["content_json"]),
            "created_at":row["created_at"],
        })
    return result

def get_lesson_by_id(lesson_id: int) -> dict | None:
    """根据 ID 查询单条教案，如果找不到就返回 None"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?",(lesson_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "topic": row["topic"],
        "grade": row["grade"],
        "content": json.loads(row["content_json"]),
        "created_at": row["created_at"]
    }
