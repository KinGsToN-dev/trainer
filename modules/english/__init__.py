import json
from difflib import SequenceMatcher
from core.models import Task, Result
from modules.base import Module

class EnglishModule(Module):
    name = "english"
    
    def load_tasks(self) -> list[Task]:
        with open("modules/english/deck.json", "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return [Task(**item) for item in data]
        
    def check(self, task: Task, user_answer: str) -> Result:
        user_clean = user_answer.lower().strip()
        correct_clean = task.answer_spec.lower().strip()
        
        if not user_clean:
            return Result(correct=False, feedback="Пустой ответ.")

        if user_clean == correct_clean:
            return Result(correct=True, feedback="Correct!")
            
        similarity = SequenceMatcher(None, user_clean, correct_clean).ratio()
        if similarity > 0.8:
            return Result(correct=True, feedback=f"Correct! (Принята опечатка, правильно: {task.answer_spec})")
            
        return Result(correct=False, feedback="Incorrect.")
