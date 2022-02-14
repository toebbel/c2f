import click
from flask.cli import with_appcontext

from c2f.call_data_storage import get_pending_callbacks, get_owning_phone_number, read_recording
from c2f.fourty_six_elks.client import elk46client


@click.command('dispatch-scheduled-calls')
@click.option('-d', '--dry-run', is_flag=True)
@with_appcontext
def dispatch_scheduled_calls(dry_run):
    pending_calls = get_pending_callbacks()
    click.echo(f"{len(pending_calls)} calls to dispatch")
    for pending in pending_calls:
        if (dry_run):
            click.echo(f"would place call {pending}")
        else:
            # elk46client.initiate_outgoing_call(pending.)
            pass

@click.command('dispatch-manual-call')
@click.argument('call_id')
@with_appcontext
def dispatch_manual_call(call_id):
    number_to_call = get_owning_phone_number(call_id)
    click.echo(f"placing call to {number_to_call}")
    elk46client.initiate_outgoing_call(number_to_call, call_id)


@click.command('extract-call')
@click.argument('call_id')
@with_appcontext
def extract_recorded_call(call_id):
    filename = "/tmp/out.mp3"
    with open(filename, 'w+b') as file:
        buffer = read_recording(call_id)
        print(buffer)
        file.write(buffer)
    click.echo(f"extracted recording of {call_id} to {filename}")

def init_app(app):
    app.cli.add_command(dispatch_scheduled_calls)
    app.cli.add_command(dispatch_manual_call)
    app.cli.add_command(extract_recorded_call)
