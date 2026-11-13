import os
from rich.console import Console
from rich.prompt import Prompt
from core.engine import run_session, run_exam, get_available_topics
from core.stats import show_stats
from core.editor import manage_cards
from core.ai_tutor import ask_ai_tutor
from modules.programming.module import ProgrammingModule
from modules.english.module import EnglishModule

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def train_subject(modules, module_name, subject_title):
    clear_screen()
    topics = get_available_topics(modules, module_name)
    
    console.print("\n[bold cyan]" + "=" * 30 + "[/bold cyan]")
    console.print(f"[bold green]{subject_title.upper()}[/bold green]")
    console.print("[bold cyan]" + "=" * 30 + "[/bold cyan]")
    console.print("0. Тренировать всё подряд")
    for i, t in enumerate(topics, 1):
        console.print(f"{i}. {t}")
    console.print("b. Назад")
    
    choice = Prompt.ask("\n[bold yellow]Выбери тему[/bold yellow]")
    
    if choice == "b":
        clear_screen()
        return
    elif choice == "0":
        run_session(modules, limit=5, target_module=module_name)
    elif choice.isdigit() and 1 <= int(choice) <= len(topics):
        selected_topic = topics[int(choice)-1]
        run_session(modules, limit=5, target_module=module_name, topic_filter=selected_topic)
    else:
        console.print("[bold red]Неверный выбор.[/bold red]")

def ai_socratic_training():
    """Режим свободного ответа с проверкой ИИ."""
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold cyan]--- РЕЖИМ СВОБОДНОГО ОТВЕТА С ИИ ---[/bold cyan]")
    console.print("[dim]Здесь нет готовых вариантов. Напиши свой развернутый ответ, а ИИ проверит логику.[/dim]")
    
    topic = console.input("\n[bold yellow]Введи тему (например, 'Рекурсия в Python' или 'Past Simple'): [/bold yellow]").strip()
    if not topic:
        return
        
    console.print("[yellow]Напиши свой ответ (нажми Enter, чтобы отправить):[/yellow]")
    answer = console.input("> ").strip()
    
    if not answer:
        return

    console.print("\n[bold magenta]ИИ анализирует твой ответ... (может занять 5-15 секунд)[/bold magenta]")
    
    feedback = ask_ai_tutor(topic, answer)
    
    console.print(f"\n[bold green]=== ОТВЕТ ИИ-ТРЕНЕРА ===[/bold green]")
    console.print(feedback)
    
    console.input("\n[dim]Нажми Enter, чтобы вернуться в меню...[/dim]")
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    modules = [ProgrammingModule(), EnglishModule()]
    
    while True:
        console.print("\n[bold cyan]" + "=" * 30 + "[/bold cyan]")
        console.print("[bold green]УНИВЕРСАЛЬНЫЙ ТРЕНАЖЕР[/bold green]")
        console.print("[bold cyan]" + "=" * 30 + "[/bold cyan]")
        console.print("1. Python (база)")
        console.print("2. English (база)")
        console.print("3. Смешанная тренировка")
        console.print("4. Экзамен (20 вопросов)")
        console.print("5. Статистика")
        console.print("6. Управление карточками")
        console.print("7. ИИ-Спарринг (Свободный ответ)")
        console.print("8. Выход")
        
        choice = Prompt.ask("\n[bold yellow]Выбери действие[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == "1":
            train_subject(modules, "programming", "Python")
        elif choice == "2":
            train_subject(modules, "english", "English")
        elif choice == "3":
            run_session(modules, limit=5)
        elif choice == "4":
            run_exam(modules, limit=20)
        elif choice == "5":
            show_stats()
        elif choice == "6":
            manage_cards()
        elif choice == "7":
            ai_socratic_training()
        elif choice == "8":
            console.print("[bold green]До связи! Не забывай тренироваться.[/bold green]")
            break

if __name__ == "__main__":
    main()
