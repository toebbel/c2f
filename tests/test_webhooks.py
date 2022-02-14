from datetime import datetime

import pytest

from c2f.call_data_storage import list_call_events, EVENT_CALL_INITIALIZED, EVENT_RECORDING_CONSENT
from c2f.db import get_db
import uuid
import json


class FourtySixElksActions(object):
    def __init__(self, client, ):
        self._client = client

    def initiateCall(self, from_number='+4612121212', to_number='+09887766', call_id=None):
        if call_id is None:
            call_id = str(uuid.uuid4())
        initData = {
            'to': to_number,
            'from': from_number,
            'callid': call_id,
        }
        return call_id, self._client.post('/calls/incoming/initiate', data=initData)

    def startRecording(self, from_number='+4612121212', to_number='+09887766', call_id=None):
        if call_id is None:
            call_id = str(uuid.uuid4())
        payload = {
            'to': to_number,
            'from': from_number,
            'callid': call_id,
        }
        return call_id, self._client.post('/calls/incoming/start-loop', data=payload)

    def giveConsent(self, from_number='+4612121212', to_number='+09887766', call_id=None):
        return self.keepRecording(result='1', from_number=from_number, to_number=to_number, call_id=call_id)

    def keepRecording(self, result=None, from_number='+4612121212', to_number='+09887766', call_id=None):
        if call_id is None:
            call_id = str(uuid.uuid4())
        payload = {
            'to': to_number,
            'from': from_number,
            'callid': call_id,
            'result': result
        }
        return call_id, self._client.post('/calls/incoming/loop', data=payload)


    def selectScheduleOption(self, result=None, from_number='+4612121212', to_number='+09887766', call_id=None):
        if call_id is None:
            call_id = str(uuid.uuid4())
        payload = {
            'to': to_number,
            'from': from_number,
            'callid': call_id,
            'result': result
        }
        return call_id, self._client.post('/calls/incoming/schedule', data=payload)


@pytest.fixture
def forty_six_elks(client):
    return FourtySixElksActions(client)


def test_initiate_incoming_call(forty_six_elks, app):
    call_id, response = forty_six_elks.initiateCall(from_number='+46121212', to_number='+01223344')
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'https://localhost/calls/incoming/start-loop'
    assert body['play'] == 'https://localhost/static/greeting.mp3'

    with app.app_context():
        events = list_call_events(call_id)
        assert len(events) == 1
        assert events[0]['owner_number'].endswith('+46121212')
        assert events[0]['event_type'] == EVENT_CALL_INITIALIZED


def test_start_recording(forty_six_elks, app):
    call_id, _ = forty_six_elks.initiateCall()
    _, response = forty_six_elks.startRecording(call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['recordcall'] == 'https://localhost/calls/incoming/complete'
    assert body['next'] == 'https://localhost/calls/incoming/loop'
    assert body['ivr'] == 'https://localhost/static/silence.mp3'


def test_keep_recording(forty_six_elks, app):
    call_id, _ = forty_six_elks.initiateCall()
    _, response = forty_six_elks.startRecording(call_id=call_id)
    _, response = forty_six_elks.keepRecording(call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'https://localhost/calls/incoming/loop'
    assert body['ivr'] == 'https://localhost/static/silence.mp3'

    with app.app_context():
        # no event type 'consent' in event list
        events = list_call_events(call_id)
        assert len(events) == 1
        assert events[0]['event_type'] == EVENT_CALL_INITIALIZED

    # user consents to the recording
    _, response = forty_six_elks.keepRecording(result='1', call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'https://localhost/calls/incoming/schedule-options'
    assert body['play'] == 'https://localhost/static/post-recording-instructions.mp3'

    with app.app_context():
        # consent stored in event list
        events = list_call_events(call_id)
        assert len(events) == 2
        assert events[1]['event_type'] == EVENT_RECORDING_CONSENT


def test_schedule_call(forty_six_elks, app):
    call_id, _ = forty_six_elks.initiateCall()
    _ = forty_six_elks.giveConsent(call_id=call_id)
    _, response = forty_six_elks.selectScheduleOption(result='3', call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['play'] == 'https://localhost/static/bye.mp3'
    assert body['next'] == 'https://localhost/calls/incoming/hang-up'
    with app.app_context():
        db = get_db()
        scheduled = db.execute("SELECT scheduled_for FROM recordings WHERE call_id = ?", (call_id, )).fetchone()[0]
        diff = (scheduled - datetime.now()).total_seconds()
        diff_days = round(diff / (60 * 60 * 24))
        assert diff_days == 3

