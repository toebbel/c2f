from flask import (
    Blueprint, request, jsonify
)
from c2f.fourty_six_elks import (explainer, recording_loop, schedule_playback_explainer, end_call)

from c2f.db import get_db

bp = Blueprint('webhooks', __name__, url_prefix='/calls/incoming')


@bp.route('/initiate', methods=['POST'])
def initiate_incoming_call():
    caller_number = request.form['from']
    call_id = request.form['callid']
    if call_id is None or caller_number is None:
        return "invalid request", 400
    db = get_db()
    statement = "INSERT INTO call_events (call_id, owner_number, event_type) VALUES (?, ?,'call_started')"
    db.execute(statement, (call_id, caller_number))
    db.commit()
    print(f"[{call_id}] call initiated")
    return jsonify(explainer())


@bp.route('/start-loop', methods=['POST'])
def start_recording():
    data = request.form
    print(f"start recording {data}")
    loop_counter = 0
    return jsonify(recording_loop(loop_counter))


@bp.route('/loop', methods=['POST'])
def keep_recording():
    loop_counter = request.args.get('loopCount', default=1, type=int)
    data = request.form
    print(f"alive? counter {loop_counter}, request {data}")
    if (data['result'] == '1'):
        return jsonify(schedule_playback_explainer())

    loop_counter += 1
    return jsonify(recording_loop(loop_counter))


@bp.route('/end', methods=['POST'])
def hang_up():
    data = request.form
    print("hanging up")
    return jsonify(end_call())


@bp.route('/complete', methods=['POST'])
def incoming_recording_complete():
    data = request.form
    print(f"complete. {data}")
    call_id = data['callid']
    completed = data['created']
    wav_url = data['wav']
    print(f"call {call_id} completed @ {completed}. Sound file: ${wav_url}")
    return "ok"
