from datetime import timezone
import datetime
from sqlite3 import Binary

from c2f.db import get_db

EVENT_CALL_INITIALIZED = 'incoming_call_initiated'
EVENT_RECORDING_CONSENT = 'recording_consent'
EVENT_CALL_COMPLETED = 'incoming_call_completed'
EVENT_RECORDING_DELIVERED = 'outgoing_call_succeeded'
EVENT_RECORDING_FAILED = 'outgoing_call_attempt_failed'
EVENT_RECORDING_FAILED_PERMANENTLY = 'outgoing_call_failed_permanently'

def list_call_events(call_id):
    db = get_db()
    result = db.execute("SELECT * from call_events WHERE call_id = ? ORDER BY observed_at ASC", (call_id, )).fetchall()
    return result

def add_initial_call_event(call_id, calling_phone_number, now=datetime.datetime.now(timezone.utc)):
    """when a new incoming call is made"""
    db = get_db()
    statement = "INSERT INTO call_events " \
                "(call_id, owner_number, event_type, observed_at) " \
                "VALUES (?, ?, ?, ?)"
    # TODO uniqueness constraint on (call_id, event_type)
    db.execute(statement, (call_id, "tel:" + calling_phone_number, EVENT_CALL_INITIALIZED, now))
    db.commit()
    return call_id


def _add_call_event(db, call_id, event, now):
    statement = "INSERT INTO call_events (event_type, call_id, observed_at, owner_number) " \
                "SELECT :event_type as column, :call_id as column, :observed_at as column, existing.owner_number " \
                "FROM call_events existing WHERE call_id = :call_id AND event_type = :required_previous_event"
    params = {
        'event_type': event,
        'observed_at': now,
        'call_id': call_id,
        'required_previous_event': EVENT_CALL_INITIALIZED,
    }
    db.execute(statement, params)
    return call_id


def add_call_recording_consent(call_id, now=datetime.datetime.now(timezone.utc)):
    """stores the consent of a user to that we can record the call"""
    db = get_db()
    result = _add_call_event(db, call_id, EVENT_RECORDING_CONSENT, now)
    statement = "INSERT INTO recordings  (call_id, created_at, owner_number) " \
                "SELECT :call_id as column, :created_at as column, events.owner_number " \
                "FROM call_events events WHERE call_id = :call_id AND event_type = :init_event_type"
    params = {
        'call_id': call_id,
        'created_at': now,
        'init_event_type': EVENT_CALL_INITIALIZED,
    }
    db.execute(statement, params)
    db.commit()
    return result

def has_call_recording_consent(call_id):
    db = get_db()
    statement = "SELECT * FROM call_events WHERE event_type = ? AND call_id = ?"
    consent_rows = db.execute(statement, (EVENT_RECORDING_CONSENT, call_id)).fetchmany(1)
    return len(consent_rows) > 0

def complete_call(call_id, now=datetime.datetime.now(timezone.utc)):
    """marks the call as completed in the database"""
    db = get_db()
    result = _add_call_event(db, call_id, EVENT_CALL_COMPLETED, now)
    db.commit()
    return result


def schedule_callback(call_id, scheduled_date):
    """when we should call back the user and play back the recording"""
    statement = "UPDATE recordings SET scheduled_for = :scheduled_for WHERE call_id = :call_id"
    db = get_db()
    db.execute(statement, {'call_id': call_id, 'scheduled_for': scheduled_date})
    db.commit()
    return call_id


def get_pending_callbacks(now=datetime.datetime.now(timezone.utc)):
    """returns a list of callbacks that are scheduled now"""
    statement = "SELECT call_id, owner_number from recordings " \
                "WHERE scheduled_for < :now AND delivered = false"
    db = get_db()
    result = db.execute(statement, {'now': now}).fetchall()
    prefix = 'tel:'
    pending_callbacks = []
    for row in [dict(r) for r in result]:
        number = row['owner_number'][len(prefix):]
        row.update({'owner_number': number})
        pending_callbacks.append(row)
    return pending_callbacks


def callback_succeeded(call_id, now=datetime.datetime.now(timezone.utc)):
    """we could reach the user and play back the recording"""
    db = get_db()
    _add_call_event(db, call_id, EVENT_RECORDING_DELIVERED, now)
    statement = "UPDATE recordings SET delivered = true WHERE call_id = :call_id"
    db.execute(statement, {'call_id': call_id})
    db.commit()
    return call_id


def callback_failed(call_id, now=datetime.datetime.now(timezone.utc)):
    """we could not reach the user or failed to play back the recording

    The call will be re-scheduled to be dispatched 24 hours after the initial scheduled time.
    """
    db = get_db()
    params = {'call_id': call_id}
    select_all_attempts = "SELECT COUNT(observed_at) FROM call_events WHERE call_id = :call_id"
    attempts = db.execute(select_all_attempts, params).fetchone()[0]
    if attempts > 3:
        _add_call_event(db, call_id, EVENT_RECORDING_FAILED_PERMANENTLY, now)
        statement = "UPDATE recordings SET scheduled_for = NULL, failed_permanently = true WHERE call_id = :call_id"
        db.execute(statement, params)
    else:
        _add_call_event(db, call_id, EVENT_RECORDING_FAILED, now)
        statement = "UPDATE recordings SET scheduled_for = DATETIME(scheduled_for, '+1 days') WHERE call_id = :call_id"
        db.execute(statement, params)
    db.commit()
    return call_id

def store_recording(call_id, audio_buffer):
    db = get_db()
    statement = "UPDATE recordings SET storage_blob = ? WHERE call_id = ?"
    db.execute(statement, (Binary(audio_buffer), call_id))
    db.commit()

def read_recording(call_id):
    db = get_db()
    statement = "SELECT storage_blob FROM recordings WHERE call_id = ?"
    result = db.execute(statement, (call_id, )).fetchone()
    return result[0]
