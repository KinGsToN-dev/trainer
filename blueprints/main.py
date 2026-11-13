from flask import Blueprint, render_template, request, redirect, url_for, send_file
from core.db import get_connection, get_player_xp, get_player_rank, get_streak, get_activity_heatmap
from core.achievements import get_achievements
import os, zipfile, io
from services.task_manager import get_all_trainable_tasks

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    all_tasks = get_all_trainable_tasks()
    with get_connection() as conn:
        total_attempts = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        correct = conn.execute("SELECT COUNT(*) FROM attempts WHERE correct = 1").fetchone()[0]
    accuracy = (correct / total_attempts * 100) if total_attempts > 0 else 0
    return render_template('index.html', total=total_attempts, accuracy=round(accuracy, 1), db_size=len(all_tasks), xp=get_player_xp(), rank=get_player_rank(get_player_xp()))

@main_bp.route('/profile')
def profile():
    xp = get_player_xp(); streak = get_streak(); heatmap = get_activity_heatmap(28)
    achievements, lang_tasks, solved_task_ids = get_achievements()
    lang_stats = {}
    for lang, task_ids in lang_tasks.items():
        solved_in_lang = sum(1 for tid in task_ids if tid in solved_task_ids)
        lang_stats[lang] = {"total": len(task_ids), "solved": solved_in_lang, "percent": round((solved_in_lang / len(task_ids)) * 100) if len(task_ids) > 0 else 0}
    return render_template('profile.html', xp=xp, rank=get_player_rank(xp), streak=streak, heatmap=heatmap, lang_stats=lang_stats, achievements=achievements)

@main_bp.route('/export')
def export_backup():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists("data/trainer.db"): zf.write("data/trainer.db", "data/trainer.db")
        zf.write("modules/code_challenges.json", "modules/code_challenges.json")
        zf.write("modules/programming/deck.json", "modules/programming/deck.json")
        zf.write("modules/english/deck.json", "modules/english/deck.json")
    memory_file.seek(0)
    return send_file(memory_file, download_name="trainer_backup.zip", as_attachment=True, mimetype='application/zip')

@main_bp.route('/import', methods=['POST'])
def import_backup():
    if 'backup_file' not in request.files: return "Файл не найден", 400
    file = request.files['backup_file']
    if file.filename == '' or not file.filename.endswith('.zip'): return "Неверный формат файла.", 400
    try:
        with zipfile.ZipFile(file, 'r') as zf:
            for member in zf.infolist():
                if member.filename.startswith(('data/', 'modules/')): zf.extract(member, path=".")
        return redirect(url_for('main.index', import_success="true"))
    except Exception as e: return f"Ошибка: {e}", 500
