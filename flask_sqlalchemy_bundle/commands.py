import click

from flask_alembic.cli.click import cli as db
from flask.cli import with_appcontext

from .extensions import alembic, db as db_ext


@db.command('drop')
@click.option('--drop', is_flag=True, expose_value=True,
              prompt='Drop DB tables?')
@with_appcontext
def drop_command(drop):
    """Drop database tables."""
    if not drop:
        exit('Cancelled.')

    click.echo('Dropping DB tables.')
    drop_all()

    click.echo('Done.')


def drop_all():
    db_ext.drop_all()
    db_ext.engine.execute('DROP TABLE IF EXISTS alembic_version;')


@db.command('reset')
@click.option('--reset', is_flag=True, expose_value=True,
              prompt='Drop DB tables and run migrations?')
@with_appcontext
def reset_command(reset):
    """Drop database tables and run migrations."""
    if not reset:
        exit('Cancelled.')

    click.echo('Dropping DB tables.')
    drop_all()

    click.echo('Running DB migrations.')
    alembic.upgrade()

    click.echo('Done.')
