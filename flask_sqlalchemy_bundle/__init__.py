from flask_unchained import Bundle

from .alembic import MaterializedViewMigration
from .decorators import param_converter
from .extensions import db
from .services import ModelManager, SessionManager
from .sqla.metaclass import _ModelRegistry


class FlaskSQLAlchemyBundle(Bundle):
    name = 'flask_sqlalchemy_bundle'
    command_group_names = ['db']

    @classmethod
    def after_init_app(cls, app):
        _ModelRegistry.finish_initializing()
