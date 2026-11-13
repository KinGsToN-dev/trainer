import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from core.models import ReviewState, Attempt

DB_FILE = "data/trainer.db"

# ИСПРАВЛЕНИЕ: Используем contextmanager для закрытия соединения
@contextmanager
def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close() # Теперь соединение ВСЕГДА закрывается

def init_db():
    with get_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS review (task_id TEXT PRIMARY KEY, ease REAL, interval_days INTEGER, due_date TEXT, lapses INTEGER, streak INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, timestamp TEXT, user_answer TEXT, correct BOOLEAN)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS player_stats (id INTEGER PRIMARY KEY CHECK (id = 1), xp INTEGER DEFAULT 0)''')
        conn.execute('''INSERT OR IGNORE INTO player_stats (id, xp) VALUES (1, 0)''')

def get_review_state(task_id: str) -> ReviewState:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM review WHERE task_id = ?", (task_id,)).fetchone()
        if row: return ReviewState(**dict(row))
        return ReviewState(task_id=task_id, due_date="2020-01-01")

def save_review_state(state: ReviewState):
    with get_connection() as conn:
        conn.execute('''INSERT OR REPLACE INTO review (task_id, ease, interval_days, due_date, lapses, streak) VALUES (?, ?, ?, ?, ?, ?)''', (state.task_id, state.ease, state.interval_days, state.due_date, state.lapses, state.streak))

def save_attempt(attempt: Attempt):
    with get_connection() as conn:
        conn.execute('''INSERT INTO attempts (task_id, timestamp, user_answer, correct) VALUES (?, ?, ?, ?)''', (attempt.task_id, attempt.timestamp.isoformat(), attempt.user_answer, attempt.correct))

def delete_task_progress(task_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM review WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM attempts WHERE task_id = ?", (task_id,))

def get_player_xp() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT xp FROM player_stats WHERE id = 1").fetchone()
        return row["xp"] if row else 0

def add_player_xp(amount: int):
    with get_connection() as conn:
        conn.execute("UPDATE player_stats SET xp = xp + ? WHERE id = 1", (amount,))

def get_player_rank(xp: int) -> str:
    if xp < 100: return "🐣 Новичок"
    if xp < 300: return "⚔️ Джуниор"
    if xp < 600: return "🛡️ Мидл"
    if xp < 1000: return "🔥 Сеньор"
    return "👑 Архитектор"

def get_streak() -> int:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT DATE(timestamp) as day FROM attempts ORDER BY day DESC").fetchall()
    if not rows: return 0
    streak = 0; today = datetime.now().date()
    dates = [datetime.strptime(r["day"], "%Y-%m-%d").date() for r in rows]
    if dates[0] < today - timedelta(days=1): return 0
    current_date = dates[0]
    for d in dates:
        if d == current_date: streak += 1; current_date -= timedelta(days=1)
        else: break
    return streak

def get_activity_heatmap(days: int = 28) -> dict:
    today = datetime.now().date(); start_date = today - timedelta(days=days)
    with get_connection() as conn:
        rows = conn.execute("SELECT DATE(timestamp) as day, COUNT(*) as count FROM attempts WHERE DATE(timestamp) >= ? GROUP BY DATE(timestamp)", (start_date.isoformat(),)).fetchall()
    activity = {row["day"]: row["count"] for row in rows}
    heatmap = []
    for i in range(days + 1):
        day = (start_date + timedelta(days=i)).isoformat()
        heatmap.append({"date": day, "count": activity.get(day, 0)})
    return heatmap

init_db()
