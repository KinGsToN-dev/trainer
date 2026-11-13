import os
from rich.console import Console
from rich.table import Table
from core.db import get_connection

console = Console()

def show_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        if total == 0:
            console.print("\n[bold yellow]Пока нет данных для статистики.[/bold yellow]")
            console.input("\n[dim]Нажми Enter, чтобы вернуться в меню...[/dim]")
            os.system('cls' if os.name == 'nt' else 'clear')
            return
            
        correct = conn.execute("SELECT COUNT(*) FROM attempts WHERE correct = 1").fetchone()[0]
        accuracy = (correct / total) * 100
        unique_cards = conn.execute("SELECT COUNT(*) FROM review").fetchone()[0]
        
        # Убрали эмодзи из заголовка
        table = Table(title="Твоя статистика", show_header=True, header_style="bold magenta")
        table.add_column("Метрика", style="cyan")
        table.add_column("Значение", style="green")
        
        table.add_row("Всего ответов", str(total))
        table.add_row("Правильных", f"{correct} ({accuracy:.1f}%)")
        table.add_row("Изучено карточек", str(unique_cards))
        
        console.print("\n")
        console.print(table)
        
        bad_rows = conn.execute('''
            SELECT task_id, COUNT(*) as error_count 
            FROM attempts 
            WHERE correct = 0 
            GROUP BY task_id 
            ORDER BY error_count DESC 
            LIMIT 3
        ''').fetchall()
        
        if bad_rows:
            # Убрали эмодзи
            bad_table = Table(title="Топ ошибок (надо подтянуть)", show_header=True, header_style="bold red")
            bad_table.add_column("ID Задачи")
            bad_table.add_column("Кол-во ошибок")
            for row in bad_rows:
                bad_table.add_row(row["task_id"], str(row["error_count"]))
            console.print(bad_table)

    console.input("\n[dim]Нажми Enter, чтобы вернуться в меню...[/dim]")
    os.system('cls' if os.name == 'nt' else 'clear')
