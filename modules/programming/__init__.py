import json
from difflib import SequenceMatcher
from core.models import Task, Result
from modules.base import Module

class ProgrammingModule(Module):
    name = "programming"
    
    def load_tasks(self) -> list[Task]:
        with open("modules/programming/deck.json", "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return [Task(**item) for item in data]
        
    def check(self, task: Task, user_answer: str) -> Result:
        user_clean = user_answer.lower().strip().replace(" ", "")
        correct_clean = task.answer_spec.lower().strip().replace(" ", "")
        
        if not user_clean:
            return Result(correct=False, feedback="Пустой ответ.")

        # Если совпадает точь-в-точь
        if user_clean == correct_clean:
            return Result(correct=True, feedback="Верно!")
            
        # Проверка на опечатки (схожесть > 80%)
        similarity = SequenceMatcher(None, user_clean, correct_clean).ratio()
        if similarity > 0.8:
            return Result(correct=True, feedback=f"Верно! (Принята опечатка, правильное написание: {task.answer_spec})")
            
        return Result(correct=False, feedback="Ошибка.")
