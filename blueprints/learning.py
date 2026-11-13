from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from core.db import get_connection, get_review_state, save_review_state, save_attempt, add_player_xp
from core.scheduler import update_review_state
from core.models import Attempt
from services.task_manager import get_all_trainable_tasks, load_code_challenges, execute_code_check, check_qa_answer
from datetime import datetime
import random

learning_bp = Blueprint('learning', __name__)

def get_subject_data():
    all_tasks = get_all_trainable_tasks()
    subject_data = {}
    for t in all_tasks:
        subj = t["module"]
        if subj not in subject_data: subject_data[subj] = {"topics": set(), "diffs": set()}
        subject_data[subj]["topics"].add(t["topic"])
        subject_data[subj]["diffs"].add(t["difficulty"])
    for subj in subject_data:
        subject_data[subj]["topics"] = sorted(list(subject_data[subj]["topics"]))
        subject_data[subj]["diffs"] = sorted(list(subject_data[subj]["diffs"]))
    return subject_data

@learning_bp.route('/train')
def train_settings():
    return render_template('train_settings.html', subject_data=get_subject_data())

@learning_bp.route('/start_training', methods=['POST'])
def start_training():
    all_tasks = get_all_trainable_tasks()
    sel_module = request.form.get('module', 'all')
    sel_topic = request.form.get('topic', 'all')
    sel_diff = request.form.get('difficulty', 'all')
    
    try:
        limit = int(request.form.get('limit', 10))
    except ValueError:
        limit = 10
        
    force = request.form.get('ignore_srs') == 'on'
    
    # 1. Фильтруем все задачи по параметрам
    filtered = [t for t in all_tasks if 
                (sel_module == 'all' or t["module"] == sel_module) and 
                (sel_topic == 'all' or t["topic"] == sel_topic) and 
                (sel_diff == 'all' or str(t["difficulty"]) == sel_diff)]
    
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    if force:
        # Если игнорируем график, берем все подряд
        session_tasks = filtered
    else:
        # Иначе берем созревшие, и если их мало — добираем несозревшие
        due = [t for t in filtered if get_review_state(t["id"]).due_date <= today]
        not_due = [t for t in filtered if get_review_state(t["id"]).due_date > today]
        
        # Сначала перемешиваем обе группы, потом склеиваем (созревшие идут первыми)
        random.shuffle(due)
        random.shuffle(not_due)
        session_tasks = due + not_due
    
    random.shuffle(session_tasks)
    
    if not session_tasks: 
        return render_template('train.html', error="Нет задач для тренировки по выбранным параметрам!", can_force=bool(filtered), form_data=request.form)
        
    session['task_ids'] = [t["id"] for t in session_tasks[:limit]]
    session['current_idx'] = 0
    session['score'] = 0
    return redirect(url_for('learning.question'))

@learning_bp.route('/question', methods=['GET', 'POST'])
def question():
    all_tasks = get_all_trainable_tasks()
    if 'task_ids' not in session or session['current_idx'] >= len(session['task_ids']): return redirect(url_for('learning.summary'))
    idx = session['current_idx']
    task = next((t for t in all_tasks if t["id"] == session['task_ids'][idx]), None)
    if not task: session['current_idx'] += 1; return redirect(url_for('learning.question'))
    fb, corr, ans = None, False, ""
    if request.method == 'POST':
        ans = request.form.get('answer', '').strip()
        if task["type"] == "qa":
            corr = check_qa_answer(ans, task["answer_spec"])
            fb = "✅ Верно!" if corr else f"❌ Ошибка. Правильный ответ: {task['answer_spec']}"
        else:
            challenge = next((c for c in load_code_challenges() if c["id"] == task["id"]), None)
            if challenge:
                corr, fb = execute_code_check(challenge, ans)
                if corr: add_player_xp(challenge.get("xp", 10))
            else:
                corr, fb = False, "Ошибка: задача не найдена."
        if corr: session['score'] += 1
        save_review_state(update_review_state(get_review_state(task["id"]), corr))
        save_attempt(Attempt(task["id"], datetime.now(), ans, corr))
        session['current_idx'] += 1; session.modified = True
    return render_template('train.html', task=task, feedback=fb, is_correct=corr, user_answer=ans, current_num=idx + 1, total_num=len(session['task_ids']))

@learning_bp.route('/summary')
def summary():
    score, total = session.get('score', 0), len(session.get('task_ids', []))
    session.pop('task_ids', None); session.pop('current_idx', None); session.pop('score', None)
    return render_template('summary.html', score=score, total=total)

@learning_bp.route('/exam')
def exam_settings():
    return render_template('exam_settings.html', subject_data=get_subject_data())

@learning_bp.route('/start_exam', methods=['POST'])
def start_exam():
    all_tasks = get_all_trainable_tasks()
    try:
        limit = int(request.form.get('limit', 20))
    except ValueError:
        limit = 20
        
    sel_module = request.form.get('module', 'all')
    sel_topic = request.form.get('topic', 'all')
    sel_diff = request.form.get('difficulty', 'all')
    
    filtered = [t for t in all_tasks if 
                (sel_module == 'all' or t["module"] == sel_module) and 
                (sel_topic == 'all' or t["topic"] == sel_topic) and 
                (sel_diff == 'all' or str(t["difficulty"]) == sel_diff)]
    
    random.shuffle(filtered)
    exam_tasks = filtered[:limit]
    
    if not exam_tasks:
        return render_template('train.html', error="Нет задач для экзамена по выбранным параметрам.")
        
    session['exam_task_ids'] = [t["id"] for t in exam_tasks]
    session['exam_results'] = {} 
    return redirect(url_for('learning.exam_dashboard'))

@learning_bp.route('/exam_dashboard')
def exam_dashboard():
    if 'exam_task_ids' not in session: return redirect(url_for('learning.exam_settings'))
    all_tasks = get_all_trainable_tasks()
    results = session.get('exam_results', {})
    data = []
    for idx, t_id in enumerate(session['exam_task_ids']):
        task = next((t for t in all_tasks if t["id"] == t_id), None)
        if task:
            status = "correct" if results.get(t_id) else ("incorrect" if t_id in results else "unanswered")
            data.append({"idx": idx, "id": t_id, "status": status, "short_prompt": task["prompt"][:30] + "...", "task": task})
    return render_template('exam_dashboard.html', tasks=data, total=len(session['exam_task_ids']))

@learning_bp.route('/api/check_answer', methods=['POST'])
def api_check_answer():
    all_tasks = get_all_trainable_tasks()
    data = request.json; idx = int(data.get('idx')); ans = data.get('answer', '').strip()
    t_id = session['exam_task_ids'][idx]
    task = next((t for t in all_tasks if t["id"] == t_id), None)
    
    if task["type"] == "qa":
        correct = check_qa_answer(ans, task["answer_spec"])
        feedback = "Верно!" if correct else "Ошибка."
        answer_spec = task["answer_spec"]
    else:
        challenge = next((c for c in load_code_challenges() if c["id"] == task["id"]), None)
        if challenge:
            correct, feedback = execute_code_check(challenge, ans)
            answer_spec = "Код"
        else:
            correct, feedback, answer_spec = False, "Ошибка", ""
            
    session['exam_results'][t_id] = correct; session.modified = True
    save_attempt(Attempt(task["id"], datetime.now(), ans, correct))
    return jsonify({"correct": correct, "feedback": feedback, "answer_spec": answer_spec})

@learning_bp.route('/finish_exam')
def finish_exam():
    results = session.get('exam_results', {})
    score = sum(1 for is_correct in results.values() if is_correct)
    total = len(session.get('exam_task_ids', []))
    session.pop('exam_task_ids', None); session.pop('exam_results', None)
    return render_template('exam_summary.html', score=score, total=total)
