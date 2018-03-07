from flask_unchained import Bundle

from .alembic import MaterializedViewMigration
from .decorators import param_converter
from .extensions import SQLAlchemy, db
from .services import ModelManager, SessionManager
from .sqla import BaseModel, QueryBaseModel


class FlaskSQLAlchemyBundle(Bundle):
    name = 'flask_sqlalchemy_bundle'
    command_group_names = ['db']

    @classmethod
    def after_init_app(cls, app):
        from .sqla.metaclass import _model_registry
        _model_registry.finalize_mappings()
