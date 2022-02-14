from flask import (
    Blueprint, request, jsonify, send_file
)
from markupsafe import escape


from c2f.call_data_storage import read_recording, callback_succeeded, callback_failed
from c2f.fourty_six_elks import (end_call, play_greeting, play_recording_audio)

import io
from c2f.db import get_db

bp = Blueprint('webhooks_outgoing', __name__, url_prefix='/calls/outgoing')


@bp.route('/greet/<recorded_call_id>', methods=['POST'])
def greeting(recorded_call_id):
    rcid = escape(recorded_call_id)
    call_id = request.form['callid']
    print(f"[{call_id}] playing greeting for recorded call {rcid}")
    return jsonify(play_greeting(rcid))

@bp.route('/playback/<recorded_call_id>', methods=['POST'])
def play_recording(recorded_call_id):
    call_id = request.form['callid']
    rcid = escape(recorded_call_id)
    print(f"[{call_id}] playing recording of original call {rcid}")
    return jsonify(play_recording_audio(rcid))

@bp.route('/playback-audio/<recorded_call_id>', methods=['GET'])
def recorded_audio(recorded_call_id):
    rcid = escape(recorded_call_id)
    print(f"audio recording of original call {rcid} is fetched")
    audio = read_recording(rcid)
    return send_file(io.BytesIO(audio), mimetype='audio/mpeg')

@bp.route('/end/<recorded_call_id>', methods=['POST'])
def hang_up(recorded_call_id):
    call_id = request.form['callid']
    rcid = escape(recorded_call_id)
    print(f"[{call_id}] received {str(request.form)} on /end recorded call {rcid}")
    return jsonify(end_call())

@bp.route('/completed/<recorded_call_id>', methods=['POST'])
def hung_up(recorded_call_id):
    call_id = request.form['id']
    rcid = escape(recorded_call_id)
    duration = int(request.form['duration'])
    if duration > 15: # TODO this should be not hard-coded
        print(f"[{call_id} delivered recorded call {rcid}")
        callback_succeeded(rcid)
    else:
        print(f"[{call_id} failed to deliver recorded call {rcid}. Will re-schedule.")
        callback_failed(rcid)
    return '', 200

