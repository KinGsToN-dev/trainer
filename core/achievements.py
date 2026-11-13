import json
from core.db import get_connection

def get_achievements():
    """Считает достижения на основе решенных задач."""
    with open("modules/code_challenges.json", "r", encoding="utf-8-sig") as f:
        challenges = json.load(f)
        
    with get_connection() as conn:
        # Получаем все успешные попытки
        attempts = conn.execute("SELECT task_id FROM attempts WHERE correct = 1").fetchall()
    
    solved_task_ids = set(a["task_id"] for a in attempts)
    
    # Группируем задачи по языкам
    lang_tasks = {}
    for c in challenges:
        lang = c.get("lang", "Python")
        if lang not in lang_tasks:
            lang_tasks[lang] = []
        lang_tasks[lang].append(c["id"])
        
    achievements = []
    
    # Логика медалей для каждого языка
    for lang, task_ids in lang_tasks.items():
        total_in_lang = len(task_ids)
        solved_in_lang = sum(1 for tid in task_ids if tid in solved_task_ids)
        
        # Бронза (1 задача)
        if solved_in_lang >= 1:
            achievements.append({"lang": lang, "level": "Bronze", "title": f"Новичок {lang}", "icon": "🥉"})
        # Серебро (5 задач)
        if solved_in_lang >= 5:
            achievements.append({"lang": lang, "level": "Silver", "title": f"Уверенный {lang}", "icon": "🥈"})
        # Золото (10 задач)
        if solved_in_lang >= 10:
            achievements.append({"lang": lang, "level": "Gold", "title": f"Мастер {lang}", "icon": "🥇"})
            
    # Глобальные достижения
    if len(solved_task_ids) >= 20:
        achievements.append({"lang": "All", "level": "Global", "title": "Трудяга (20+ задач)", "icon": "🔥"})
        
    return achievements, lang_tasks, solved_task_ids
