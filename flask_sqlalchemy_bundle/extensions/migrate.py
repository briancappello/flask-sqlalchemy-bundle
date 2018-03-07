from flask_migrate import Migrate as BaseMigrate
from flask_unchained import unchained


class Migrate(BaseMigrate):
    @unchained.inject('db')
    def init_app(self, app, db):
        alembic_config = app.config.get('ALEMBIC', {})
        alembic_config.setdefault('script_location', 'db/migrations')

        super().init_app(app, db=db,
                         directory=alembic_config.get('script_location'),
                         **app.config.get('ALEMBIC_CONTEXT', {}))
