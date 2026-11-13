import json
import subprocess
import sys
import tempfile
import os
import shutil
from difflib import SequenceMatcher
from modules.programming.module import ProgrammingModule
from modules.english.module import EnglishModule

modules = [ProgrammingModule(), EnglishModule()]

def check_qa_answer(user_answer: str, correct_answer: str) -> bool:
    """Универсальная проверка ответов для любых QA-карточек (с защитой от опечаток)."""
    user_clean = user_answer.lower().strip().replace(" ", "")
    correct_clean = correct_answer.lower().strip().replace(" ", "")
    if not user_clean: return False
    if user_clean == correct_clean: return True
    # Прощаем опечатки (схожесть > 80%)
    return SequenceMatcher(None, user_clean, correct_clean).ratio() > 0.8

def load_code_challenges():
    with open("modules/code_challenges.json", "r", encoding="utf-8-sig") as f: 
        return json.load(f)

def get_all_trainable_tasks():
    tasks = []
    for c in load_code_challenges():
        task_dict = {
            "id": c["id"], "module": c.get("lang", "Python"), 
            "topic": c.get("topic", "general"), "difficulty": c.get("difficulty", 1), 
            "prompt": c.get("description", ""), 
            "answer_spec": c.get("reference_sql", "") if c.get("lang") == "SQL" else "Код", 
            "type": "code"
        }
        if c.get("lang") == "SQL" and "setup_sql" in c:
            task_dict["setup_sql"] = c["setup_sql"]
        tasks.append(task_dict)
        
    # Загружаем QA карточки (и Python, и English, и любые новые)
    for mod in modules:
        for t in mod.load_tasks():
            tasks.append({
                "id": t.id, "module": t.module, # Делаем красивое имя (Programmming -> Programming)
                "topic": t.topic, "difficulty": t.difficulty, 
                "prompt": t.prompt, "answer_spec": t.answer_spec, "type": "qa"
            })
            
    # Подтягиваем кастомные QA карточки, если они лежат в code_challenges.json под видом QA
    # (На случай если мы будем хранить их там)
    return tasks

def execute_code_check(challenge, user_code):
    lang = challenge.get('lang', 'Python')
    if lang == "SQL":
        setup_sql = challenge.get('setup_sql', '')
        reference_sql = challenge.get('reference_sql', '')
        if not setup_sql or not reference_sql: return False, "❌ Ошибка: в задаче нет setup_sql или reference_sql."
        full_code = f"""
import sqlite3
conn = sqlite3.connect(':memory:'); cursor = conn.cursor()
try: cursor.executescript('''{setup_sql}''')
except Exception as e: print("SETUP_ERROR:", str(e)); exit(1)
try: cursor.execute('''{reference_sql}'''); expected = [list(row) for row in cursor.fetchall()]
except Exception as e: print("REF_SQL_ERROR:", str(e)); exit(1)
try: cursor.execute('''{user_code}'''); actual = [list(row) for row in cursor.fetchall()]
except Exception as e: print("SQL_ERROR:", str(e)); exit(1)
if actual == expected: print('ALL_TESTS_PASSED')
else: print(f"ASSERTION_ERROR: Ожидалось {{expected}}, получено {{actual}}")
"""
        config = {"ext": ".py", "cmd": [sys.executable]}; ext = ".py"
    else:
        config = {"Python": {"ext": ".py", "cmd": [sys.executable]}, "JS": {"ext": ".js", "cmd": ["node"]}, "PHP": {"ext": ".php", "cmd": ["php"]}}.get(lang, {"ext": ".py", "cmd": [sys.executable]})
        ext = config["ext"]
        if shutil.which(config["cmd"][0]) is None: return False, f"❌ Ошибка: Интерпретатор {lang} не установлен."
        if lang == "Python": full_code = user_code + "\n\n# --- ТЕСТЫ ---\n" + "\n".join(challenge["tests"]) + "\nprint('ALL_TESTS_PASSED')\n"
        elif lang == "JS": full_code = user_code + "\n\n// --- ТЕСТЫ ---\n" + "\n".join(challenge["tests"]) + "\nconsole.log('ALL_TESTS_PASSED');\n"
        elif lang == "PHP":
            if not user_code.strip().startswith("<?php"): user_code = "<?php\n" + user_code
            full_code = user_code + "\n\n// --- ТЕСТЫ ---\n" + "\n".join(challenge["tests"]) + "\necho 'ALL_TESTS_PASSED';\n"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode="w", encoding="utf-8") as f:
        f.write(full_code); temp_path = f.name
    env = os.environ.copy(); env['PYTHONIOENCODING'] = 'utf-8'
    try:
        result = subprocess.run(config["cmd"] + [temp_path], capture_output=True, text=True, timeout=3, env=env, encoding='utf-8')
        if "ALL_TESTS_PASSED" in result.stdout:
            return True, f"✅ Все тесты пройдены!"
        else:
            err_msg = result.stderr
            if "REF_SQL_ERROR:" in result.stdout: return False, "❌ Ошибка в сгенерированной задаче: ИИ написал эталонный запрос к несуществующим колонкам."
            elif "SETUP_ERROR:" in result.stdout: err_msg = "Ошибка в таблицах: " + result.stdout.split("SETUP_ERROR:")[1].strip()
            elif "SQL_ERROR:" in result.stdout: err_msg = "Ошибка SQL: " + result.stdout.split("SQL_ERROR:")[1].strip()
            elif "ASSERTION_ERROR:" in result.stdout: err_msg = result.stdout.split("ASSERTION_ERROR:")[1].strip()
            elif "AssertionError:" in err_msg: err_msg = err_msg.split("AssertionError:")[1].strip().split("\n")[0]
            elif "Error:" in err_msg: err_msg = err_msg.split("Error:")[1].strip().split("\n")[0]
            return False, f"❌ Тест провален:\n{err_msg}"
    except subprocess.TimeoutExpired: return False, "❌ Таймаут!"
    finally: os.remove(temp_path)

