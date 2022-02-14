from c2f.call_data_storage import add_initial_call_event, add_call_recording_consent, EVENT_RECORDING_CONSENT, \
    complete_call, EVENT_CALL_COMPLETED, schedule_callback, get_pending_callbacks, callback_succeeded, callback_failed, \
    store_recording, read_recording
from c2f.db import get_db
from datetime import datetime, timezone
from datetime import timedelta
import os

from tests.test_audio_editor import binary_compare

_call_id = "some call id"
_number = "+46123456789"


def test_add_initial_call_event(app):
    with app.app_context():
        add_initial_call_event(_call_id, _number)
        stored_event = get_db().execute("SELECT * FROM call_events").fetchall()
        assert len(stored_event) == 1
        assert stored_event[0]['call_id'] == _call_id
        assert stored_event[0]['owner_number'] == "tel:" + _number


def test_add_call_recording_consent__no_consent_when_call_not_initialixed(app):
    with app.app_context():
        add_call_recording_consent(_call_id)
        stored_event = get_db().execute("SELECT * FROM call_events WHERE event_type = ?",
                                        (EVENT_RECORDING_CONSENT,)).fetchall()
        assert len(stored_event) == 0


def test_add_call_recording_consent(app):
    with app.app_context():
        # multiple calls going on at the same time
        add_initial_call_event(_call_id + "1", _number + "1")
        add_initial_call_event(_call_id + "2", _number + "2")
        add_initial_call_event(_call_id, _number)

        add_call_recording_consent(_call_id)
        stored_event = get_db().execute("SELECT * FROM call_events WHERE event_type = ?",
                                        (EVENT_RECORDING_CONSENT,)).fetchall()
        assert len(stored_event) == 1
        assert stored_event[0]['call_id'] == _call_id
        # correct owner number
        assert stored_event[0]['owner_number'] == "tel:" + _number


def test_complete_call__event_is_inserted(app):
    with app.app_context():
        add_initial_call_event(_call_id, _number)

        complete_call(_call_id)
        stored_event = get_db().execute("SELECT * FROM call_events WHERE event_type = ?",
                                        (EVENT_CALL_COMPLETED,)).fetchall()
        assert len(stored_event) == 1
        assert stored_event[0]['call_id'] == _call_id
        assert stored_event[0]['owner_number'] == "tel:" + _number


def test_schedule_and_get_pending_callbacks(app):
    with app.app_context():
        callid2 = "call id 2"
        add_initial_call_event(_call_id, _number)
        add_initial_call_event(callid2, _number)
        complete_call(_call_id)
        complete_call(callid2)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        schedule_callback(callid2, tomorrow)
        schedule_callback(_call_id, yesterday)

        pending = get_pending_callbacks()

        assert len(pending) == 1
        assert pending[0]['call_id'] == _call_id
        assert pending[0]['owner_number'] == _number


def test_get_pending_callbacks__does_not_include_delivered_calls(app):
    with app.app_context():
        add_initial_call_event(_call_id, _number)
        complete_call(_call_id)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        schedule_callback(_call_id, yesterday)

        pending_list = get_pending_callbacks()
        assert len(pending_list) == 1
        callback_succeeded(pending_list[0]['call_id'])

        pending_list = get_pending_callbacks()
        assert len(pending_list) == 0


def test_callback_failed__reschedules_plus_one_day(app):
    with app.app_context():
        add_initial_call_event(_call_id, _number)
        complete_call(_call_id)
        now = datetime.now(timezone.utc)
        first_scheduled_attempt = now - timedelta(hours=25)
        schedule_callback(_call_id, first_scheduled_attempt)

        pending_list = get_pending_callbacks()
        assert len(pending_list) == 1
        callback_failed(pending_list[0]['call_id'], now)

        statement = "SELECT scheduled_for from recordings " \
                    "WHERE delivered = false AND call_id = ?"
        db = get_db()
        rescheduled = db.execute(statement, (_call_id,)).fetchone()[0]
        in_one_hour = (first_scheduled_attempt + timedelta(days=1)).replace(tzinfo=None, microsecond=0)
        assert rescheduled == in_one_hour


def test_callback_failed__fails_permanent_after_fourth_attempt(app):
    with app.app_context():
        add_initial_call_event(_call_id, _number)
        complete_call(_call_id)
        callback_failed(_call_id)
        callback_failed(_call_id)
        callback_failed(_call_id)
        callback_failed(_call_id)

        statement = "SELECT scheduled_for from recordings " \
                    "WHERE failed_permanently = true AND call_id = ?"
        db = get_db()
        failed = db.execute(statement, (_call_id,)).fetchall()
        assert len(failed) == 1
        assert failed[0][0] is None

def test_store_and_read_recording(app):
    in_path = os.path.join(os.path.dirname(__file__), 'test-expected-output.mp3')
    out_path = os.path.join(os.path.dirname(__file__), 'test-actual-database-output.mp3')
    with app.app_context(), open(in_path, 'rb') as in_file, open(out_path, 'wb') as out_file:
        add_initial_call_event(_call_id, _number)
        complete_call(_call_id)

        store_recording(_call_id, in_file.read())
        buffer = read_recording(_call_id)
        out_file.write(buffer)
    assert binary_compare(in_path, out_path)