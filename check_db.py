import json
import os
import sqlite3

def check_db():
    print("=== АУДИТ БАЗЫ ДАННЫХ ===\n")
    
    # 1. Проверка JSON файлов
    files = {
        "Python QA": "modules/programming/deck.json",
        "English QA": "modules/english/deck.json",
        "Code Challenges": "modules/code_challenges.json"
    }
    
    total_tasks = 0
    for name, path in files.items():
        if not os.path.exists(path):
            print(f"❌ Файл {name} не найден!")
            continue
            
        with open(path, "r", encoding="utf-8-sig") as f:
            try:
                tasks = json.load(f)
                total_tasks += len(tasks)
                print(f"✅ {name}: {len(tasks)} задач")
                
                # Проверка на пустые поля
                empty_fields = 0
                for t in tasks:
                    if not t.get("prompt") and not t.get("title"):
                        empty_fields += 1
                if empty_fields > 0:
                    print(f"   ⚠️ Внимание: {empty_fields} задач без вопроса/названия!")
            except Exception as e:
                print(f"❌ Ошибка чтения {name}: {e}")
                
    print(f"\nВсего задач в JSON: {total_tasks}")
    
    # 2. Проверка SQLite БД
    print("\n=== ПРОВЕРКА SQLITE ===")
    if not os.path.exists("data/trainer.db"):
        print("❌ База данных trainer.db не найдена!")
        return
        
    with sqlite3.connect("data/trainer.db") as conn:
        cursor = conn.cursor()
        
        # Считаем количество записей
        cursor.execute("SELECT COUNT(*) FROM attempts")
        attempts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM review")
        reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT xp FROM player_stats WHERE id = 1")
        xp = cursor.fetchone()
        
        print(f"✅ Всего попыток ответов (attempts): {attempts}")
        print(f"✅ Карточек в планировщике (review): {reviews}")
        print(f"✅ Текущий XP: {xp[0] if xp else 0}")
        
        # Проверка "осиротевших" записей (удаленные карточки)
        cursor.execute("SELECT DISTINCT task_id FROM review")
        review_ids = set(r[0] for r in cursor.fetchall())
        
        all_json_ids = set()
        for path in files.values():
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8-sig") as f:
                    for t in json.load(f):
                        if "id" in t: all_json_ids.add(t["id"])
                        
        orphaned = review_ids - all_json_ids
        if orphaned:
            print(f"⚠️ Найдены {len(orphaned)} записей прогресса для удаленных карточек. (Можно почистить)")
        else:
            print("✅ Прогресс синхронизирован с задачами (нет осиротевших записей).")
            
    print("\nАудит завершен!")

if __name__ == "__main__":
    check_db()
