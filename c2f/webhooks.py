import tempfile
from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, request, jsonify
)

from c2f.audio_editor import convert_and_clip
from c2f.call_data_storage import add_initial_call_event, add_call_recording_consent, complete_call, store_recording, \
    has_call_recording_consent, schedule_callback
from c2f.fourty_six_elks import (explainer, recording_loop, schedule_playback_explainer, end_call,
                                 schedule_playback_menu, thanks_and_bye)
from c2f.fourty_six_elks.client import elk46client

bp = Blueprint('webhooks', __name__, url_prefix='/calls/incoming')


@bp.route('/initiate', methods=['POST'])
def initiate_incoming_call():
    caller_number = request.form['from']
    call_id = request.form['callid']
    if call_id is None or caller_number is None:
        return "invalid request", 400
    add_initial_call_event(call_id, caller_number)
    print(f"[{call_id}] call initiated")
    return jsonify(explainer())


@bp.route('/start-loop', methods=['POST'])
def start_recording():
    call_id = request.form['callid']
    if call_id is None:  # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400
    print(f"[{call_id}] starting loop")  # put logging into the middleware, too?
    loop_counter = 0
    return jsonify(recording_loop(loop_counter))


@bp.route('/loop', methods=['POST'])
def keep_recording():
    loop_counter = request.args.get('loopCount', default=1, type=int)
    data = request.form
    call_id = data['callid']
    if call_id is None:  # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400

    consent = False
    if 'result' in data:
        consent = str(data['result']) == '1'

    print(f"[{call_id}] IVR consent result: {consent}, loop count {loop_counter}")
    if consent:
        add_call_recording_consent(call_id)
        print(f"[{call_id}] stored recording consent")
        return jsonify(schedule_playback_explainer())
    loop_counter += 1
    return jsonify(recording_loop(loop_counter))


@bp.route('/schedule-options', methods=['POST'])
def schedule_options():
    data = request.form
    call_id = data['callid']
    if call_id is None:  # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400
    return jsonify(schedule_playback_menu())


@bp.route('/schedule', methods=['POST'])
def schedule_choice():
    data = request.form
    call_id = data['callid']
    if call_id is None:  # can this be put into some middleware? we always need callid in webhook calls
        return "invalid request", 400
    scheduling_choice = 2  # default
    if 'result' in data:
        scheduling_choice = int(data['result'])

    # this is the default of option '2'
    delta = timedelta(days=3) # TODO randomize 'within 7 days'
    if scheduling_choice == 1:
        delta = timedelta(hours=1)
    elif scheduling_choice == 3:
        timedelta(days=15) # TODO randomize 'within 30 days'
    else:
        timedelta(days=45)  # TODO randomize 'within 90 days'

    scheduled_for = datetime.now(timezone.utc) + delta
    schedule_callback(call_id, scheduled_for)
    print(f"[{call_id}] scheduled call for {scheduled_for}")
    return jsonify(thanks_and_bye())

@bp.route('/hang-up', methods=['POST'])
def hang_up():
    data = request.form
    call_id = data['callid']
    print(f"[{call_id}] hanging up")
    return jsonify(end_call())


@bp.route('/complete', methods=['POST'])
def incoming_recording_complete():
    data = request.form
    call_id = data['callid']
    completed_at = data['created']
    duration = data['duration']

    complete_call(call_id)

    if not has_call_recording_consent(call_id):
        print(f"call {call_id} completed @ {completed_at}, duration {duration}. User did not give recording consent")
        return "ok"

    wav_url = data['wav']
    wav_file = elk46client.download_recording(wav_url)
    # TODO we could check, how much audio we should actually crop. We do not account for repeated scheduling
    # instructions, waiting on user input, or network delays. But the amount we cut off is the minimum.

    temp_mp3_file = tempfile.TemporaryFile(mode='w+b')
    convert_and_clip(wav_file, temp_mp3_file, 26 * 1000, 23 * 1000)
    store_recording(call_id, temp_mp3_file.read())

    print(f"call {call_id} completed @ {completed_at}, duration: ${duration}. Recording stored.")
    return "ok"
