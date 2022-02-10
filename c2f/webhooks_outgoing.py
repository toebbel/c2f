from flask import (
    Blueprint, request, jsonify
)
from c2f.fourty_six_elks import (end_call, play_greeting, playback)

from c2f.db import get_db

bp = Blueprint('webhooks_outgoing', __name__, url_prefix='/calls/outgoing')


@bp.route('/greet', methods=['POST'])
def greeting():
    call_id = request.form['callid']
    print(f"[{call_id}] playing greeting")
    return jsonify(play_greeting())

@bp.route('playback', methods=['POST'])
def play_recording():
    call_id = request.form['callid']
    print(f"[{call_id}] playing greeting")
    return jsonify(playback('foo'))

@bp.route('end', methods=['POST'])
def hang_up():
    print(f"received {str(request.form)} on /end")
    return jsonify(end_call())

@bp.route('/completed', methods=['POST'])
def hung_up():
    print(f"received {str(request.form)} on /completed")

    # TODO There we should fetch the call legs from 46elks to verify that the webhooks are authentic
    # db = get_db()
    # statement = "INSERT INTO call_events (call_id, owner_number, event_type) VALUES (?, ?,'call_started')"
    # db.execute(statement, (call_id, caller_number))
    # db.commit()
    print(f"[{request.form}] call hung up")
    return '', 200
