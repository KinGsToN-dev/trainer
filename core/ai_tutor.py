import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console

console = Console()
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Trainer"})
MODEL = "openrouter/free"

def ask_ai_for_hint(question: str, user_answer: str) -> dict:
    if not api_key: return {"error": "API ключ не найден."}
    system_prompt = (
        "Ты — опытный учитель. Ученик пытается ответить на вопрос. "
        "Дай подсказку или наводящий вопрос, который поможет найти правильный ответ. "
        "НЕ ДАВАЙ прямой ответ. Если ученик написал что-то неверное, мягко укажи на ошибку. "
        "Отвечай кратко (до 3-4 предложений) на русском языке."
    )
    user_prompt = f"Вопрос: {question}\n\nВвод ученика: {user_answer if user_answer else '(пусто)'}"
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7
        )
        return {"hint": response.choices[0].message.content, "model": response.model if hasattr(response, 'model') else "openrouter/auto"}
    except Exception as e:
        return {"error": str(e)}

def review_code(task_description: str, user_code: str) -> dict:
    if not api_key: return {"error": "API ключ не найден."}
    system_prompt = "Ты — опытный Senior-разработчик. Сделай код-ревью. Укажи на слабые места, предложи улучшения."
    user_prompt = f"Задача: {task_description}\n\nКод ученика:\n```\n{user_code}\n```"
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7
        )
        return {"review": response.choices[0].message.content, "model": response.model if hasattr(response, 'model') else "openrouter/auto"}
    except Exception as e:
        return {"error": str(e)}

def generate_ai_code_challenges_batch(lang: str, topic: str, difficulty: int, count: int) -> dict:
    if not api_key: return {"error": "API ключ не найден."}
    
    # ИСПРАВЛЕНИЕ: Внутри строк используем одинарные кавычки для JSON
    if lang.upper() == "SQL":
        system_prompt = (
            "Ты — эксперт по SQL. Сгенерируй массив задач и верни ТОЛЬКО валидный JSON-массив без markdown. "
            "Формат: [{'title': 'Название', 'lang': 'SQL', 'topic': 'Тема', 'difficulty': 1, 'description': 'Описание задачи', 'hint': 'Подсказка', 'starter_code': '-- Напиши запрос\\n', 'setup_sql': 'CREATE TABLE...', 'reference_sql': 'SELECT...', 'xp': 15}]. "
            "КРИТИЧЕСКОЕ ПРАВИЛО: Все три поля (setup_sql, reference_sql, starter_code) должны быть на SQL."
        )
    else:
        test_instructions = {"Python": "assert func(2) == 4", "JS": "if (func(2) !== 4) throw new Error()", "PHP": "if (func(2) !== 4) throw new Exception()"}
        instruction = test_instructions.get(lang, test_instructions["Python"])
        system_prompt = (
            f"Ты — эксперт по языку {lang}. Сгенерируй массив задач в формате JSON без markdown. "
            f"Формат: [{{'title': 'Название', 'lang': '{lang}', 'topic': 'Тема', 'difficulty': 1, 'description': 'Описание', 'hint': 'Подсказка', 'starter_code': 'def func():\\n    pass', 'tests': ['{instruction}'], 'xp': 15}}]. "
            f"КРИТИЧЕСКОЕ ПРАВИЛО: {instruction}"
        )
        
    user_prompt = f"Сгенерируй ровно {count} задач. Категория: {lang}. Тема: {topic}."
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        start = content.find('['); end = content.rfind(']') + 1
        if start == -1 or end == 0: return {"error": "ИИ вернул ответ без JSON."}
        challenges = json.loads(content[start:end])
        return {"challenges": challenges, "model": response.model if hasattr(response, 'model') else "openrouter/auto"}
    except Exception as e:
        return {"error": str(e)}

def generate_qa_cards_batch(subject: str, topic: str, difficulty: int, count: int) -> dict:
    """Генерирует простые карточки Вопрос-Ответ для тренировок."""
    if not api_key: return {"error": "API ключ не найден."}
    
    system_prompt = (
        "Ты — эксперт по созданию обучающих карточек. Верни ТОЛЬКО валидный JSON-массив без markdown. "
        "Формат каждого элемента: {"
        '"topic": "короткая тема", '
        '"prompt": "вопрос", '
        '"answer_spec": "очень короткий ответ (1-3 слова)", '
        f'"difficulty": {difficulty}'
        "}. "
        f"Сгенерируй вопросы для предмета '{subject}' по теме '{topic}'. "
        "Ответы должны быть однозначными и простыми для проверки."
    )
    user_prompt = f"Сгенерируй ровно {count} карточек. Тема: {topic}."
    
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        start = content.find('['); end = content.rfind(']') + 1
        if start == -1 or end == 0: return {"error": "ИИ вернул ответ без JSON."}
        cards = json.loads(content[start:end])
        return {"cards": cards, "model": response.model if hasattr(response, 'model') else "openrouter/auto"}
    except Exception as e:
        return {"error": str(e)}
