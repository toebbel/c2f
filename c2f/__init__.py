import os

from flask import Flask, request, jsonify
from c2f.fourty_six_elks import explainer, recording_loop, schedule_playback_explainer, end_call

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
        return jsonify(explainer())
    
    @app.route('/calls/incoming/start-loop', methods=['POST'])
    def start_recording():
        data = request.form
        print(f"start recording {data}")
        loop_counter = 0
        return jsonify(recording_loop(loop_counter))

    
    @app.route('/calls/incoming/loop', methods=['POST'])
    def keep_recording():
        loop_counter = request.args.get('loopCount', default = 1, type = int)
        data = request.form
        print(f"alive? counter {loop_counter}, request {data}")
        if (data['result'] == '1'):
            return jsonify(schedule_playback_explainer())
        
        loop_counter += 1
        return jsonify(recording_loop(loop_counter))
    

    @app.route('/calls/incoming/end', methods=['POST'])
    def hang_up():
        data = request.form
        print("hanging up")
        return jsonify(end_call())

    @app.route('/calls/incoming/complete', methods=['POST'])
    def incoming_recording_complete():
        data = request.form
        print(f"complete. {data}")
        call_id = data['callid']
        completed = data['created']
        wav_url = data['wav']
        print(f"call {call_id} completed @ {completed}. Sound file: ${wav_url}")
        return "ok"


    from . import db
    db.init_app(app)
    return app