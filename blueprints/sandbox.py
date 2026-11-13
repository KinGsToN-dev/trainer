from flask import Blueprint, render_template, request, jsonify
from core.db import get_player_xp, get_player_rank, add_player_xp
from core.ai_tutor import generate_ai_code_challenges_batch, review_code, ask_ai_for_hint
from services.task_manager import load_code_challenges, execute_code_check
import json, subprocess, sys, tempfile, os, shutil

sandbox_bp = Blueprint('sandbox', __name__)

@sandbox_bp.route('/code_runner')
def code_runner():
    challenges = load_code_challenges()
    lang_topics = {}
    for c in challenges:
        l = c.get('lang', 'Python'); t = c.get('topic', 'general')
        if l not in lang_topics: lang_topics[l] = set()
        lang_topics[l].add(t)
    lang_topics = {k: sorted(list(v)) for k, v in lang_topics.items()}
    diffs = sorted(list(set(c.get('difficulty', 1) for c in challenges)))
    return render_template('code_runner.html', challenges=challenges, lang_topics=lang_topics, diffs=diffs, xp=get_player_xp(), rank=get_player_rank(get_player_xp()))

@sandbox_bp.route('/ai_generator')
def ai_generator():
    challenges = load_code_challenges()
    lang_topics = {}
    for c in challenges:
        l = c.get('lang', 'Python'); t = c.get('topic', 'general')
        if l not in lang_topics: lang_topics[l] = set()
        lang_topics[l].add(t)
    lang_topics = {k: sorted(list(v)) for k, v in lang_topics.items()}
    return render_template('ai_generator.html', lang_topics=lang_topics)

@sandbox_bp.route('/api/get_hint', methods=['POST'])
def get_hint():
    data = request.json
    result = ask_ai_for_hint(data.get('question'), data.get('user_input', ''))
    if "error" in result: return jsonify({"success": False, "message": result["error"]})
    return jsonify({"success": True, "hint": result["hint"], "model": result["model"]})

@sandbox_bp.route('/api/check_code', methods=['POST'])
def check_code_api():
    data = request.json
    user_code, challenge_id = data.get('code', ''), data.get('challenge_id')
    challenge = next((c for c in load_code_challenges() if c["id"] == challenge_id), None)
    if not challenge: return jsonify({"error": "Задача не найдена"}), 404
    correct, msg = execute_code_check(challenge, user_code)
    if correct: add_player_xp(challenge.get("xp", 10))
    return jsonify({"success": correct, "message": msg})

@sandbox_bp.route('/api/generate_preview', methods=['POST'])
def api_generate_preview():
    data = request.json
    lang, topic = data.get('lang', 'Python'), data.get('topic', 'General')
    difficulty, count = int(data.get('difficulty', 1)), int(data.get('count', 1))
    result = generate_ai_code_challenges_batch(lang, topic, difficulty, count)
    if "error" in result: return jsonify({"success": False, "message": result["error"]})
    return jsonify({"success": True, "challenges": result["challenges"], "model": result["model"]})

@sandbox_bp.route('/api/review_code', methods=['POST'])
def api_review_code():
    data = request.json
    user_code, challenge_id = data.get('code', ''), data.get('challenge_id')
    challenge = next((c for c in load_code_challenges() if c["id"] == challenge_id), None)
    if not challenge: return jsonify({"success": False, "message": "Задача не найдена."})
    if not user_code.strip(): return jsonify({"success": False, "message": "Напиши хоть какой-то код."})
    result = review_code(challenge["description"], user_code)
    if "error" in result: return jsonify({"success": False, "message": result["error"]})
    return jsonify({"success": True, "review": result["review"], "model": result["model"]})

@sandbox_bp.route('/api/save_generated', methods=['POST'])
def api_save_generated():
    data = request.json
    new_challenges = data.get('challenges', [])
    selected_difficulty = int(data.get('difficulty', 1))
    challenges = load_code_challenges()
    base_id = len(challenges) + 1
    for i, ch in enumerate(new_challenges):
        ch['id'] = f"code_{base_id + i:03d}"
        ch['difficulty'] = selected_difficulty
        if 'xp' not in ch: ch['xp'] = 10 * selected_difficulty
        challenges.append(ch)
    with open("modules/code_challenges.json", "w", encoding="utf-8") as f: json.dump(challenges, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})

@sandbox_bp.route('/api/run_code', methods=['POST'])
def run_code():
    data = request.json
    code, lang = data.get('code', ''), data.get('lang', 'Python')
    if not code.strip(): return jsonify({"output": "", "error": "Код пуст."})
    if lang == "SQL": return jsonify({"output": "Для проверки SQL нажми 'Сдать решение'.", "error": ""})
    config = {"Python": {"ext": ".py", "cmd": [sys.executable]}, "JS": {"ext": ".js", "cmd": ["node"]}, "PHP": {"ext": ".php", "cmd": ["php"]}}.get(lang, {"ext": ".py", "cmd": [sys.executable]})
    if shutil.which(config["cmd"][0]) is None: return jsonify({"error": f"Ошибка: Интерпретатор {lang} не найден."})
    if lang == "PHP" and not code.strip().startswith("<?php"): code = "<?php\n" + code
    with tempfile.NamedTemporaryFile(delete=False, suffix=config["ext"], mode="w", encoding="utf-8") as f:
        f.write(code); temp_path = f.name
    env = os.environ.copy(); env['PYTHONIOENCODING'] = 'utf-8'
    try:
        result = subprocess.run(config["cmd"] + [temp_path], capture_output=True, text=True, timeout=3, env=env, encoding='utf-8')
        return jsonify({"output": result.stdout, "error": result.stderr})
    except subprocess.TimeoutExpired: return jsonify({"error": "Ошибка: Превышено время."})
    finally: os.remove(temp_path)
