from modules.programming.module import ProgrammingModule
from modules.english.module import EnglishModule
from core.models import Task

def test_programming_checker_fuzzy():
    mod = ProgrammingModule()
    task = Task(id="1", module="programming", topic="t", type="qa", prompt="p", answer_spec="print", difficulty=1)
    
    # Точное совпадение
    assert mod.check(task, "print").correct is True
    # Игнорирование регистра и пробелов
    assert mod.check(task, "  PRINT  ").correct is True
    # Опечатка (схожесть > 80%)
    assert mod.check(task, "prnt").correct is True
    # Полная чушь
    assert mod.check(task, "hello").correct is False

def test_english_checker_fuzzy():
    mod = EnglishModule()
    task = Task(id="1", module="english", topic="t", type="qa", prompt="p", answer_spec="apple", difficulty=1)
    
    assert mod.check(task, "apple").correct is True
    assert mod.check(task, "Apple ").correct is True
    assert mod.check(task, "aple").correct is True # Опечатка
    assert mod.check(task, "banana").correct is False
