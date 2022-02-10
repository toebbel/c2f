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
    # TODO move the database actions to the webhook that receives the cording. There we should fetch the call legs from 46elks to verify that the webhooks are authentic
    db = get_db()
    statement = "INSERT INTO call_events (call_id, owner_number, event_type) VALUES (?, ?,'call_started')"
    db.execute(statement, (call_id, caller_number))
    db.commit()
    print(f"[{call_id}] call initiated")
    return jsonify(explainer())


@bp.route('/start-loop', methods=['POST'])
def start_recording():
    call_id = request.form['callid']
    if call_id is None: # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400
    print(f"[{call_id}] starting loop") # put logging into the middleware, too?
    loop_counter = 0
    return jsonify(recording_loop(loop_counter))


@bp.route('/loop', methods=['POST'])
def keep_recording():
    loop_counter = request.args.get('loopCount', default=1, type=int)
    data = request.form
    call_id = data['callid']
    caller_number = data['from']
    if call_id is None or caller_number is None:  # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400

    consent = False
    if 'result' in data:
        consent = str(data['result']) == '1'

    print(f"[{call_id}] IVR consent result: {consent}, loop count {loop_counter}")
    if consent:
        # TODO move the database actions to the webhook that receives the cording. There we should fetch the call legs from 46elks to verify that the webhooks are authentic
        db = get_db()
        statement = "INSERT INTO call_events (call_id, owner_number, event_type) VALUES (?, ?,'record_consent')"
        db.execute(statement, (call_id, caller_number))
        db.commit()
        return jsonify(schedule_playback_explainer())
    loop_counter += 1
    return jsonify(recording_loop(loop_counter))


@bp.route('/end', methods=['POST'])
def hang_up():
    data = request.form
    call_id = data['callid']
    print(f"[{call_id}] hanging up")
    return jsonify(end_call())


@bp.route('/complete', methods=['POST'])
def incoming_recording_complete():
    data = request.form
    print(f"complete. {data}")
    call_id = data['callid']
    completed = data['created']
    # TODO download, convert to mp3 and store the file
    # TODO cut the wav file so that intro and outro are not included
    print(f"call {call_id} completed @ {completed}. Payload: ${completed}")
    return "ok"

