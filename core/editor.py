import json
import os
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from core.db import delete_task_progress
from core.ai_tutor import generate_ai_tasks

console = Console()

def get_deck_info(module_name):
    if module_name == "programming": return "modules/programming/deck.json", "py_"
    else: return "modules/english/deck.json", "en_"

def load_deck(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f: return json.load(f)

def save_deck(file_path, deck):
    with open(file_path, "w", encoding="utf-8") as f: json.dump(deck, f, ensure_ascii=False, indent=2)

def display_deck(deck, title="Текущая база задач"):
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("№", justify="right", style="dim")
    table.add_column("ID", style="yellow")
    table.add_column("Тема", style="green")
    table.add_column("Сл.", justify="center")
    table.add_column("Вопрос (начало)", style="white")
    for i, card in enumerate(deck, 1):
        short_prompt = card['prompt'][:40] + "..." if len(card['prompt']) > 40 else card['prompt']
        table.add_row(str(i), card['id'], card['topic'], str(card['difficulty']), short_prompt)
    console.print(table)

def select_module():
    console.print("\n1. Python\n2. English")
    choice = Prompt.ask("Выбери предмет", choices=["1", "2"])
    return "programming" if choice == "1" else "english"

def add_new_card():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold cyan]--- ДОБАВЛЕНИЕ НОВОЙ КАРТОЧКИ ---[/bold cyan]")
    module_name = select_module()
    file_path, id_prefix = get_deck_info(module_name)
    deck = load_deck(file_path)
    
    existing_ids = [int(t["id"].split("_")[1]) for t in deck if t["id"].startswith(id_prefix)]
    new_id_num = max(existing_ids) + 1 if existing_ids else 1
    new_id = f"{id_prefix}{new_id_num:03d}"

    topic = console.input("[yellow]Введи тему: [/yellow]").strip()
    prompt_text = console.input("[yellow]Введи сам вопрос: [/yellow]").strip()
    answer = console.input("[yellow]Введи правильный ответ: [/yellow]").strip()
    difficulty = IntPrompt.ask("[yellow]Сложность (1-3)[/yellow]", choices=["1", "2", "3"], default=1)

    deck.append({"id": new_id, "module": module_name, "topic": topic if topic else "general", "type": "qa", "prompt": prompt_text, "answer_spec": answer, "difficulty": difficulty, "tags": []})
    save_deck(file_path, deck)
    console.print(f"\n[bold green]Успешно добавлено! ID: {new_id}[/bold green]")
    console.input("\n[dim]Нажми Enter...[/dim]")

def edit_card():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold cyan]--- РЕДАКТИРОВАНИЕ КАРТОЧКИ ---[/bold cyan]")
    module_name = select_module()
    file_path, _ = get_deck_info(module_name)
    deck = load_deck(file_path)
    if not deck:
        console.print("[bold red]База пуста![/bold red]")
        return

    display_deck(deck, "Выбери карточку для изменения")
    card_num = IntPrompt.ask("\n[bold yellow]Введи НОМЕР карточки[/bold yellow]")
    if 1 <= card_num <= len(deck):
        card = deck[card_num - 1]
        console.print(f"\nТекущий вопрос: [green]{card['prompt']}[/green]")
        console.print(f"Текущий ответ: [green]{card['answer_spec']}[/green]")
        new_prompt = console.input("[yellow]Новый вопрос (Enter - оставить): [/yellow]").strip()
        new_answer = console.input("[yellow]Новый ответ (Enter - оставить): [/yellow]").strip()
        if new_prompt: card['prompt'] = new_prompt
        if new_answer: card['answer_spec'] = new_answer
        save_deck(file_path, deck)
        console.print(f"\n[bold green]Обновлено![/bold green]")
    console.input("\n[dim]Нажми Enter...[/dim]")

def delete_card():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold cyan]--- УДАЛЕНИЕ КАРТОЧКИ ---[/bold cyan]")
    module_name = select_module()
    file_path, _ = get_deck_info(module_name)
    deck = load_deck(file_path)
    if not deck:
        console.print("[bold red]База пуста![/bold red]")
        return

    display_deck(deck, "Выбери карточку для удаления")
    card_num = IntPrompt.ask("\n[bold yellow]Введи НОМЕР карточки[/bold yellow]")
    if 1 <= card_num <= len(deck):
        card = deck[card_num - 1]
        if Prompt.ask(f"[bold red]Удалить '{card['id']}'?[/bold red]", choices=["y", "n"]) == "y":
            deck.pop(card_num - 1)
            save_deck(file_path, deck)
            delete_task_progress(card['id'])
            console.print(f"\n[bold green]Удалено.[/bold green]")
    console.input("\n[dim]Нажми Enter...[/dim]")

def generate_cards():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold magenta]--- ГЕНЕРАЦИЯ ЗАДАЧ ЧЕРЕЗ ИИ ---[/bold magenta]")
    console.print("[dim]ИИ придумает вопросы и автоматически добавит их в базу.[/dim]")
    
    module_name = select_module()
    file_path, id_prefix = get_deck_info(module_name)
    deck = load_deck(file_path)

    topic = console.input("\n[yellow]По какой теме генерировать? (например: PHP, SQL, JS, Linux CLI): [/yellow]").strip()
    count = IntPrompt.ask("[yellow]Сколько вопросов сгенерировать? (советую 5-10)[/yellow]", default=5)
    diff = IntPrompt.ask("[yellow]Сложность (1-3)[/yellow]", choices=["1", "2", "3"], default=1)

    # ИСПРАВЛЕНО: теперь теги совпадают (открываем cyan, закрываем cyan)
    console.print("\n[bold cyan]Отправляем запрос в ИИ... Это может занять 10-20 секунд.[/bold cyan]")
    
    new_tasks = generate_ai_tasks(topic, count, diff)

    if not new_tasks:
        console.print("[bold red]ИИ не смог сгенерировать задачи или произошла ошибка. Попробуй еще раз.[/bold red]")
        console.input("\n[dim]Нажми Enter...[/dim]")
        return

    existing_ids = [int(t["id"].split("_")[1]) for t in deck if t["id"].startswith(id_prefix)]
    next_id = max(existing_ids) + 1 if existing_ids else 1

    added_count = 0
    for t in new_tasks:
        new_card = {
            "id": f"{id_prefix}{next_id:03d}",
            "module": module_name,
            "topic": t.get("topic", topic),
            "type": "qa",
            "prompt": t.get("prompt", "Вопрос не сгенерирован"),
            "answer_spec": t.get("answer_spec", "Ответ не сгенерирован"),
            "difficulty": t.get("difficulty", diff),
            "tags": ["ai-generated"]
        }
        deck.append(new_card)
        next_id += 1
        added_count += 1

    save_deck(file_path, deck)
    console.print(f"\n[bold green]Успешно добавлено {added_count} новых карточек![/bold green]")
    display_deck(deck[-added_count:], "Только что добавленные")
    console.input("\n[dim]Нажми Enter...[/dim]")

def view_all_cards():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n[bold cyan]--- ПРОСМОТР БАЗЫ ЗАДАЧ ---[/bold cyan]")
    module_name = select_module()
    file_path, _ = get_deck_info(module_name)
    deck = load_deck(file_path)
    if deck: display_deck(deck, f"Все карточки ({len(deck)} шт.)")
    else: console.print("[bold yellow]База пуста.[/bold yellow]")
    console.input("\n[dim]Нажми Enter...[/dim]")

def manage_cards():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print("\n[bold cyan]--- УПРАВЛЕНИЕ БАЗОЙ ЗАДАЧ ---[/bold cyan]")
        console.print("1. Посмотреть все карточки")
        console.print("2. Добавить новую карточку вручную")
        console.print("3. Редактировать существующую")
        console.print("4. Удалить карточку")
        console.print("5. [bold magenta]Сгенерировать задачи через ИИ[/bold magenta]")
        console.print("6. Назад в главное меню")
        
        choice = Prompt.ask("\n[bold yellow]Выбери действие[/bold yellow]", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1": view_all_cards()
        elif choice == "2": add_new_card()
        elif choice == "3": edit_card()
        elif choice == "4": delete_card()
        elif choice == "5": generate_cards()
        elif choice == "6": break
