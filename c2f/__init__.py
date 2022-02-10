import os

from flask import Flask
from . import webhooks
from . import webhooks_outgoing
from . import db
from . import cli

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True, host_matching=False)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.sqlite'),
        PREFERRED_URL_SCHEME='https',
    )

    # allow overwriting config with passed test_config
    if test_config is None:
        app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    else:
        app.config.from_mapping(test_config)

    # make sture instance folder exists;  that's where the database file will live
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    cli.init_app(app)
    app.register_blueprint(webhooks.bp)
    app.register_blueprint(webhooks_outgoing.bp)

    return app