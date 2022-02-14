import requests
import os
import tempfile

from c2f.fourty_six_elks import initiate_call


class Elk46Client:
    def __init__(self, username, password, caller_number):
        self._username = username
        self._password = password
        self._caller_number = caller_number

    def download_recording(self, wav_url):
        response = requests.get(wav_url, allow_redirects=False, auth=(self._username, self._password))
        handle, file_path = tempfile.mkstemp()
        with os.fdopen(handle, 'w+b') as wav_file:
            for chunk in response.iter_content(1024):
                wav_file.write(chunk)
        return file_path

    def initiate_outgoing_call(self, destination_phone_number, recorded_call_id):
        rsp = requests.post("https://api.46elks.com/a1/calls",
                            data=initiate_call(self._caller_number, destination_phone_number, recorded_call_id),
                            auth=(self._username, self._password))
        return rsp.status_code, rsp.reason


elk46client = Elk46Client(os.environ.get('ELK46_USER'),
                          os.environ.get('ELK46_PASSWORD'),
                          os.environ.get('ELK46_NUMBER'))
