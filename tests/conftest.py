import os
import tempfile

import pytest
from c2f import create_app
from c2f.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _sql_data_fixture = f.read().decode('utf-8')

@pytest.fixture
def app():
    db_file_descriptor, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path
    })
    with app.app_context():
        init_db()
        get_db().executescript(_sql_data_fixture)
    yield app

    os.close(db_file_descriptor)
    os.remove(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()