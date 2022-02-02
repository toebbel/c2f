from email.policy import default
import os
from flask import Flask, request, jsonify, url_for

def sound_file(name):
    return url_for('static', filename=f"{name}.mp3", _external=True)

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.sqlite'),
    )

    # allow to overwrite config with passed test_config
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # make sture instance folder exists;  that's where the database file will live
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/calls/incoming/initiate', methods=['POST'])
    def initiate_incoming_call():
        data = request.form
        print(f"initiate call {data}")
        return jsonify({
            'play': sound_file("explainer"),
            'skippable': False,
            'next': url_for('start_recording', _external=True),
        })
    
    @app.route('/calls/incoming/start-loop', methods=['POST'])
    def start_recording():
        data = request.form
        print(f"start recording {data}")
        return jsonify({
            'recordcall': url_for('incoming_recording_complete', _external=True),
            'ivr': sound_file('silence'),
            'digits': 1,
            'timeout': 30, # seconds
            'repeat': 10,  # x 10 attempts
            'next': url_for('recording_loop_condition', _external=True),
        })

    
    @app.route('/calls/incoming/alive', methods=['POST'])
    def recording_loop_condition():
        loop_counter = request.args.get('loopCount', default = 1, type = int)
        data = request.form
        print(f"alive? counter {loop_counter}, request {data}")
        if (data['result'] == '1'):
            return jsonify({
                'play': sound_file('recording-ended-thanks'),
                'next': url_for('hang_up', _external=True)
            })
        
        loop_counter += 1
        return jsonify({
            'ivr': sound_file('silence'),
            'digits': 1,
            'timeout': 30, # seconds
            'repeat': 10,  # x 10 attempts
            'next': url_for('recording_loop_condition', loopCount = loop_counter, _external=True),
        })
    

    @app.route('/calls/incoming/end', methods=['POST'])
    def hang_up():
        data = request.form
        print(f"end {data}")
        print("hanging up")
        return jsonify({
            'hangup': 'busy'
        })

    @app.route('/calls/incoming/complete', methods=['POST'])
    def incoming_recording_complete():
        data = request.form
        print(f"complete. {data}")
        call_id =data['callid']
        completed = data['created']
        wav_url = data['wav']
        print(f"call {call_id} completed @ {completed}. Sound file: ${wav_url}")
        return "ok"
    return app