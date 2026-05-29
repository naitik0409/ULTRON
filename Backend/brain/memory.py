import json
import os
import sqlite3
from datetime import datetime, timedelta
from collections import deque

MEMORY_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "memory.db")
CHAT_LOG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "ChatLog.json")


def _ensure_db():
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            category TEXT DEFAULT 'general',
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            summary TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


_ensure_db()


def initialize_chat_log():
    os.makedirs(os.path.dirname(CHAT_LOG), exist_ok=True)
    try:
        if not os.path.exists(CHAT_LOG):
            with open(CHAT_LOG, "w", encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(CHAT_LOG, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if data else []
    except (FileNotFoundError, json.JSONDecodeError):
        with open(CHAT_LOG, "w", encoding='utf-8') as f:
            json.dump([], f)
        return []


def get_conn():
    return sqlite3.connect(MEMORY_DB)


def store_fact(key: str, value: str, category: str = "general", confidence: float = 1.0):
    conn = get_conn()
    conn.execute("""
        INSERT INTO facts (key, value, category, confidence, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            confidence = excluded.confidence,
            updated_at = datetime('now')
    """, (key.lower(), value, category, confidence))
    conn.commit()
    conn.close()


def get_fact(key: str) -> str | None:
    conn = get_conn()
    cur = conn.execute("SELECT value FROM facts WHERE key = ?", (key.lower(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_facts(category: str | None = None) -> list[dict]:
    conn = get_conn()
    if category:
        cur = conn.execute("SELECT key, value, category, confidence FROM facts WHERE category = ? ORDER BY updated_at DESC", (category,))
    else:
        cur = conn.execute("SELECT key, value, category, confidence FROM facts ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"key": r[0], "value": r[1], "category": r[2], "confidence": r[3]} for r in rows]


def get_relevant_facts(query: str, limit: int = 10) -> list[dict]:
    facts = get_all_facts()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    scored = []
    for f in facts:
        score = 0
        key_words = set(f["key"].split())
        value_words = set(f["value"].lower().split())
        score += len(query_words & key_words) * 3
        score += len(query_words & value_words)
        if score > 0:
            scored.append((score, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:limit]]


def store_chat_message(role: str, content: str):
    os.makedirs(os.path.dirname(CHAT_LOG), exist_ok=True)
    try:
        if os.path.exists(CHAT_LOG):
            with open(CHAT_LOG, "r", encoding="utf-8") as f:
                chat = json.load(f)
        else:
            chat = []
    except (json.JSONDecodeError, FileNotFoundError):
        chat = []
    chat.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    with open(CHAT_LOG, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)


def get_recent_chat(n: int = 20) -> list[dict]:
    try:
        with open(CHAT_LOG, "r", encoding="utf-8") as f:
            chat = json.load(f)
        return chat[-n:]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def store_preference(key: str, value: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO preferences (key, value, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = datetime('now')
    """, (key.lower(), value))
    conn.commit()
    conn.close()


def get_preference(key: str) -> str | None:
    conn = get_conn()
    cur = conn.execute("SELECT value FROM preferences WHERE key = ?", (key.lower(),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_preferences() -> dict:
    conn = get_conn()
    cur = conn.execute("SELECT key, value FROM preferences")
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def store_daily_summary(summary: str):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    conn.execute("""
        INSERT INTO summaries (date, summary, created_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(date) DO UPDATE SET
            summary = excluded.summary,
            created_at = datetime('now')
    """, (today, summary))
    conn.commit()
    conn.close()


def get_daily_summary(date: str | None = None) -> str | None:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    cur = conn.execute("SELECT summary FROM summaries WHERE date = ?", (date,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def extract_and_store_facts(conversation: list[dict]):
    facts_text = "\n".join(f"{m['role']}: {m['content']}" for m in conversation[-10:])
    return facts_text


class ShortTermMemory:
    def __init__(self, maxlen: int = 50):
        self.messages = deque(maxlen=maxlen)

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})

    def get_recent(self, n: int = 10) -> list[dict]:
        return list(self.messages)[-n:]

    def get_formatted(self, n: int = 10) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.get_recent(n))

    def clear(self):
        self.messages.clear()
