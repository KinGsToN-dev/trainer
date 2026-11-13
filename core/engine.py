import random
import os
from datetime import datetime
from rich.console import Console
from core.models import Attempt
from core.db import get_review_state, save_review_state, save_attempt
from core.scheduler import update_review_state
from modules.base import Module

console = Console()

def get_available_topics(modules: list[Module], module_name: str):
    all_tasks = []
    for mod in modules:
        if mod.name == module_name:
            all_tasks.extend(mod.load_tasks())
    return sorted(list(set(t.topic for t in all_tasks)))

def run_session(modules: list[Module], limit: int = 5, target_module: str = None, topic_filter: str = None, diff_filter: int = None):
    # ... (существующий код сессии оставляем без изменений, я его сокращу для читаемости скрипта, но в файле он будет полным)
    # Скрипт перезапишет файл целиком.
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    all_tasks = []
    for mod in modules:
        all_tasks.extend(mod.load_tasks())
        
    filtered_tasks = []
    for task in all_tasks:
        if target_module and task.module != target_module: continue
        if topic_filter and task.topic != topic_filter: continue
        if diff_filter and task.difficulty != diff_filter: continue
        filtered_tasks.append(task)

    due_tasks = []
    for task in filtered_tasks:
        r_state = get_review_state(task.id)
        if r_state.due_date <= today:
            due_tasks.append((task, r_state))
            
    if not due_tasks:
        console.print("\n[bold yellow]По выбранным фильтрам нет задач на сегодня.[/bold yellow]")
        console.input("\n[dim]Нажми Enter...[/dim]")
        return

    random.shuffle(due_tasks)
    session_tasks = due_tasks[:limit]
    
    console.print(f"\n[bold cyan]--- НАЧАЛО СЕССИИ ({len(session_tasks)} задач) ---[/bold cyan]")
    correct_count = 0
    
    for i, (task, r_state) in enumerate(session_tasks, 1):
        console.print(f"\n[bold white]Задача {i}/{len(session_tasks)}[/bold white] | [dim]Тема: {task.topic} | Сложность: {task.difficulty}[/dim]")
        console.print(f"[bold yellow]Вопрос:[/bold yellow] {task.prompt}")
        
        user_answer = console.input("[bold green]Твой ответ (Enter для пропуска):[/bold green] ").strip()
        
        mod = next(m for m in modules if m.name == task.module)
        result = mod.check(task, user_answer)
        
        if result.correct:
            console.print(f"[bold green]✅ {result.feedback}[/bold green]")
            correct_count += 1
        else:
            console.print(f"[bold red]❌ {result.feedback}[/bold red]")
            console.print(f"[bold red]Правильный ответ: {task.answer_spec}[/bold red]")
            
        r_state = update_review_state(r_state, result.correct)
        save_review_state(r_state)
        save_attempt(Attempt(task.id, datetime.now(), user_answer, result.correct))
        
    console.print(f"\n[bold cyan]--- КОНЕЦ СЕССИИ. Верно: {correct_count} из {len(session_tasks)} ---[/bold cyan]")
    console.input("\n[dim]Нажми Enter, чтобы вернуться в меню...[/dim]")
    os.system('cls' if os.name == 'nt' else 'clear')


def run_exam(modules: list[Module], limit: int = 20):
    """Режим экзамена: случайные вопросы без учета интервалов SM-2."""
    all_tasks = []
    for mod in modules:
        all_tasks.extend(mod.load_tasks())
        
    if not all_tasks:
        console.print("\n[bold red]В базе нет задач![/bold red]")
        console.input("\n[dim]Нажми Enter...[/dim]")
        return

    random.shuffle(all_tasks)
    session_tasks = all_tasks[:limit]
    
    console.print(f"\n[bold magenta]=== РЕЖИМ ЭКЗАМЕНА ({len(session_tasks)} задач) ===[/bold magenta]")
    console.print("[dim]В этом режиме интервалы повторения не меняются. Просто проверка знаний.[/dim]")
    correct_count = 0
    
    for i, task in enumerate(session_tasks, 1):
        console.print(f"\n[bold white]Вопрос {i}/{len(session_tasks)}[/bold white] | [dim]Модуль: {task.module} | Тема: {task.topic}[/dim]")
        console.print(f"[bold yellow]Вопрос:[/bold yellow] {task.prompt}")
        
        user_answer = console.input("[bold green]Твой ответ:[/bold green] ").strip()
        
        mod = next(m for m in modules if m.name == task.module)
        result = mod.check(task, user_answer)
        
        if result.correct:
            console.print(f"[bold green]✅ {result.feedback}[/bold green]")
            correct_count += 1
        else:
            console.print(f"[bold red]❌ {result.feedback}[/bold red]")
            console.print(f"[bold red]Правильный ответ: {task.answer_spec}[/bold red]")
            
        # Сохраняем только попытку, не трогая SM-2 (review state)
        save_attempt(Attempt(task.id, datetime.now(), user_answer, result.correct))
        
    score = (correct_count / len(session_tasks)) * 100
    console.print(f"\n[bold magenta]=== ЭКЗАМЕН ОКОНЧЕН ===[/bold magenta]")
    console.print(f"Твой результат: [bold green]{correct_count} из {len(session_tasks)} ({score:.1f}%)[/bold green]")
    console.input("\n[dim]Нажми Enter, чтобы вернуться в меню...[/dim]")
    os.system('cls' if os.name == 'nt' else 'clear')
