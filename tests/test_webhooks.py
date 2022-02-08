import pytest
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

@pytest.fixture
def forty_six_elks(client):
    return FourtySixElksActions(client)


def test_initiate_incoming_call(forty_six_elks, app):
    call_id, response = forty_six_elks.initiateCall(from_number='+46121212', to_number='+01223344')
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'http://localhost/calls/incoming/start-loop'
    assert body['play'] == 'http://localhost/static/explainer.mp3'

    with app.app_context():
        expect = {'call_id': call_id, 'owner_number': 46121212, 'event_type': 'call_started'}
        stored_event = get_db().execute("SELECT * FROM call_events WHERE call_id = ?", (call_id,)).fetchone()
        assert expect['call_id'] == stored_event['call_id']
        assert expect['owner_number'] == stored_event['owner_number']
        assert expect['event_type'] == stored_event['event_type']


def test_start_recording(forty_six_elks, app):
    call_id, _ = forty_six_elks.initiateCall()
    _, response = forty_six_elks.startRecording(call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['recordcall'] == 'http://localhost/calls/incoming/complete'
    assert body['next'] == 'http://localhost/calls/incoming/loop'
    assert body['ivr'] == 'http://localhost/static/silence.mp3'


def test_keep_recording(forty_six_elks, app):
    call_id, _ = forty_six_elks.initiateCall()
    _, response = forty_six_elks.startRecording(call_id=call_id)
    _, response = forty_six_elks.keepRecording(call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'http://localhost/calls/incoming/loop'
    assert body['ivr'] == 'http://localhost/static/silence.mp3'

    # no new events stored in the database
    with app.app_context():
        stored_event = get_db().execute("SELECT * FROM call_events WHERE call_id = ? AND event_type = 'record_consent'", (call_id,)).fetchone()
        assert stored_event == None

    _, response = forty_six_elks.keepRecording(result='1', call_id=call_id)
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['next'] == 'http://localhost/calls/incoming/end'
    assert body['play'] == 'http://localhost/static/recording-ended-thanks.mp3'

    # user has consented to the recording
    with app.app_context():
        stored_event = get_db().execute("SELECT * FROM call_events WHERE call_id = ? AND event_type = 'record_consent'", (call_id,)).fetchone()
        assert call_id == stored_event['call_id']
        assert 4612121212 == stored_event['owner_number']
        assert 'record_consent' == stored_event['event_type']