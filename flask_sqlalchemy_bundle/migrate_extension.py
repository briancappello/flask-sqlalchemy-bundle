from flask_migrate import Migrate as BaseMigrate


class Migrate(BaseMigrate):
    def init_app(self, app):
        alembic_config = app.config.get('ALEMBIC', {})
        alembic_config.setdefault('script_location', 'db/migrations')

        super().init_app(app,
                         directory=alembic_config.get('script_location'),
                         **app.config.get('ALEMBIC_CONTEXT', {}))
