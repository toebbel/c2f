from flask import url_for

# response bodies that we send back to 46Elks

def sound_file(name):
    return url_for('static', filename=f"{name}.mp3", _external=True)

def explainer():
    return {
            'play': sound_file("explainer"),
            'skippable': False,
            'next': url_for('webhooks.start_recording', _external=True),
        }

def recording_loop(counter):
    start_recording  = dict()
    if (counter == 0):
        start_recording = {'recordcall': url_for('webhooks.incoming_recording_complete', _external=True)}
    return {
        'ivr': sound_file('silence'),
        'digits': 1,   # expect one key press
        'timeout': 30, # seconds
        'repeat': 10,  # x 10 attempts
        'next': url_for('keep_recording', _external=True),
    } | start_recording

def schedule_playback_explainer():
    return {
                'play': sound_file('recording-ended-thanks'),
                'next': url_for('webhooks.hang_up', _external=True)
            }

def end_call():
    {
        'hangup': 'busy'
    }