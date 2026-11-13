from flask import Blueprint, render_template, request, jsonify
from core.db import get_connection, delete_task_progress
from services.task_manager import get_all_trainable_tasks, load_code_challenges
import json

management_bp = Blueprint('management', __name__)

@management_bp.route('/manage')
def manage_cards():
    all_tasks = get_all_trainable_tasks()
    return render_template('manage.html', tasks=sorted(all_tasks, key=lambda x: (x["module"], x["id"])))

@management_bp.route('/api/clear_all_cards', methods=['POST'])
def clear_all_cards():
    with open("modules/code_challenges.json", "w", encoding="utf-8") as f: json.dump([], f)
    with open("modules/programming/deck.json", "w", encoding="utf-8") as f: json.dump([], f)
    with open("modules/english/deck.json", "w", encoding="utf-8") as f: json.dump([], f)
    with get_connection() as conn:
        conn.execute("DELETE FROM review"); conn.execute("DELETE FROM attempts")
    return jsonify({"success": True})

@management_bp.route('/api/reset_progress', methods=['POST'])
def reset_progress():
    with get_connection() as conn:
        conn.execute("DELETE FROM attempts"); conn.execute("DELETE FROM review")
        conn.execute("UPDATE player_stats SET xp = 0 WHERE id = 1")
    return jsonify({"success": True})

@management_bp.route('/api/get_card/<task_id>')
def get_card(task_id):
    if task_id.startswith('code_'): tasks = load_code_challenges()
    elif task_id.startswith('py_'):
        with open("modules/programming/deck.json", "r", encoding="utf-8-sig") as f: tasks = json.load(f)
    elif task_id.startswith('en_'):
        with open("modules/english/deck.json", "r", encoding="utf-8-sig") as f: tasks = json.load(f)
    else: return jsonify({"error": "Unknown ID"}), 404
    task = next((t for t in tasks if t.get('id') == task_id or t.get('task_id') == task_id), None)
    if not task: return jsonify({"error": "Not found"}), 404
    return jsonify(task)

@management_bp.route('/api/save_card', methods=['POST'])
def save_card():
    data = request.json
    task_id = data.get('id')
    if task_id.startswith('code_'): path = "modules/code_challenges.json"
    elif task_id.startswith('py_'): path = "modules/programming/deck.json"
    elif task_id.startswith('en_'): path = "modules/english/deck.json"
    else: return jsonify({"success": False, "message": "Неверный ID"})
    with open(path, "r", encoding="utf-8-sig") as f: tasks = json.load(f)
    index = next((i for i, t in enumerate(tasks) if t.get('id') == task_id), -1)
    if index != -1: tasks[index] = data
    else: tasks.append(data)
    with open(path, "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})

@management_bp.route('/api/delete_card', methods=['POST'])
def api_delete_card():
    task_id = request.json.get('id')
    if task_id.startswith('code_'): path = "modules/code_challenges.json"
    elif task_id.startswith('py_'): path = "modules/programming/deck.json"
    elif task_id.startswith('en_'): path = "modules/english/deck.json"
    else: return jsonify({"success": False})
    with open(path, "r", encoding="utf-8-sig") as f: tasks = json.load(f)
    tasks = [t for t in tasks if t.get('id') != task_id]
    with open(path, "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)
    delete_task_progress(task_id)
    return jsonify({"success": True})

@management_bp.route('/api/create_card', methods=['POST'])
def api_create_card():
    data = request.json
    card_type = data.get('type')
    if card_type == 'qa':
        lang = data.get('lang', 'programming')
        path = "modules/programming/deck.json" if lang == 'programming' else "modules/english/deck.json"
        prefix = "py_" if lang == 'programming' else "en_"
        with open(path, "r", encoding="utf-8-sig") as f: tasks = json.load(f)
        existing_ids = [int(t["id"].split("_")[1]) for t in tasks if t.get("id", "").startswith(prefix)]
        new_id = f"{prefix}{max(existing_ids) + 1 if existing_ids else 1:03d}"
        new_task = {"id": new_id, "module": lang, "topic": data.get('topic'), "type": "qa", "prompt": data.get('prompt'), "answer_spec": data.get('answer'), "difficulty": int(data.get('difficulty', 1)), "tags": []}
        tasks.append(new_task)
        with open(path, "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)
        return jsonify({"success": True})
    elif card_type == 'code':
        path = "modules/code_challenges.json"
        with open(path, "r", encoding="utf-8-sig") as f: tasks = json.load(f)
        base_id = len(tasks) + 1
        new_id = f"code_{base_id:03d}"
        new_task = {"id": new_id, "title": data.get('title'), "lang": data.get('lang', 'Python'), "topic": data.get('topic'), "difficulty": int(data.get('difficulty', 1)), "description": data.get('description'), "hint": data.get('hint', ''), "starter_code": data.get('starter_code', ''), "xp": 10 * int(data.get('difficulty', 1))}
        if data.get('lang') == 'SQL': new_task['setup_sql'] = data.get('setup_sql', ''); new_task['reference_sql'] = data.get('reference_sql', '')
        else: new_task['tests'] = [line.strip() for line in data.get('tests', '').split('\n') if line.strip()]
        tasks.append(new_task)
        with open(path, "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)
        return jsonify({"success": True})
