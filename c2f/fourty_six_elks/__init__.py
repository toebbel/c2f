from flask import url_for

# response bodies that we send back to 46Elks

def sound_file(name):
    return url_for('static', filename=f"{name}.mp3", _external=True)

def explainer():
    return {
            'play': sound_file("greeting"),
            'skippable': False,
            'next': url_for('webhooks.start_recording', _external=True),
        }

def recording_loop(counter):
    start_recording  = dict()
    if (counter == 0):
        start_recording = {'recordcall': url_for('webhooks.incoming_recording_complete', _external=True)}
    return {
        'ivr': sound_file('silence'),
        'digits': 1,    # expect one key press
        'timeout': 30,  # seconds
        'repeat': 10,   # x 10 attempts
        'next': url_for('webhooks.keep_recording', _external=True),
    } | start_recording

def schedule_playback_explainer():
    return {
                'play': sound_file('post-recording-instructions'),
                'next': url_for('webhooks.schedule_options', _external=True)
            }


def schedule_playback_menu():
    return {
        'ivr': sound_file('scheduling-options'),
        'digits': 1,
        'timeout': 5,
        'repeat': 4,
        'default': 2,
        'next': url_for('webhooks.schedule_choice', _external=True),
    }

def thanks_and_bye():
    return {
        'play': sound_file('bye'),
        'next': url_for('webhooks.hang_up', _external=True),
    }


def end_call():
    return {
        'hangup': 'busy'
    }

def initiate_call(from_number, to_number):
    return {
        'timeout': 40,
        'from': from_number,
        'to': to_number,
        'voice_start': url_for('webhooks_outgoing.greeting', _external=True),
        'whenhangup': url_for('webhooks_outgoing.hung_up', _external=True)
    }

def play_greeting():
    return {
        'timeout': 40,
        'play': sound_file('callback-greeting'),
        'next': url_for('webhooks_outgoing.play_recording', _external=True)
    }

def playback(recording_id):
    return {
        'next': url_for('webhooks_outgoing.hang_up', _external=True),
        'play': sound_file('recordings/' + recording_id)
    }