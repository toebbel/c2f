import os
import click
from flask.cli import with_appcontext

from c2f.fourty_six_elks import initiate_call

import requests


@click.command('make-call')
@click.option('-d', '--dry-run', is_flag=True)
@click.argument('phone_number')
@with_appcontext
def make_call_command(dry_run, phone_number):
    click.echo(f'Making call to {phone_number}')
    caller_number = "+46766860735"
    username = os.environ.get('ELK46_USER')
    password = os.environ.get('ELK46_PASSWORD')
    if dry_run:
        click.echo('would run: ' + str(initiate_call(caller_number, phone_number)))
    else:
        rsp = requests.post("https://api.46elks.com/a1/calls",
                            data=initiate_call(caller_number, phone_number),
                            auth=(username, password))
        click.echo(f'got response {rsp.status_code} {rsp.reason}')


def init_app(app):
    app.cli.add_command(make_call_command)