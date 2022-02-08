import pytest
from c2f.db import get_db
import uuid

class FourtySixElksActions(object):
    def __init__(self, client):
        self._client = client

    def initiateCall(self, from_number = '+4612121212', to_number = '+09887766'):
        call_id = str(uuid.uuid4())
        initData = {
            'to': to_number,
            'from': from_number,
            'callid': call_id,
        }
        return call_id, self._client.post('/calls/incoming/initiate', data=initData)

@pytest.fixture
def fourtySixElks(client):
    return FourtySixElksActions(client)

def test_initiate_incoming_call(fourtySixElks, app):
    call_id, response = fourtySixElks.initiateCall(from_number='+46121212', to_number='+01223344')
    assert response.status_code == 200
    assert b'/calls/incoming/start-loop' in response.data
    assert b'/explainer.mp3' in response.data

    with app.app_context():
        expect = {'call_id': call_id, 'owner_number': 46121212, 'event_type': 'call_started'}
        stored_event = get_db().execute("SELECT * FROM call_events WHERE call_id = ?", (call_id,)).fetchone()
        assert expect['call_id'] == stored_event['call_id']
        assert expect['owner_number'] == stored_event['owner_number']
        assert expect['event_type'] == stored_event['event_type']
