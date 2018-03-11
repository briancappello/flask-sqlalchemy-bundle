from flask_unchained import Bundle

from .alembic import MaterializedViewMigration
from .base_model import BaseModel
from .base_query import BaseQuery
from .decorators import param_converter
from .extensions import SQLAlchemy, db
from .services import ModelManager, SessionManager


class FlaskSQLAlchemyBundle(Bundle):
    name = 'flask_sqlalchemy_bundle'
    command_group_names = ['db']

    @classmethod
    def after_init_app(cls, app):
        from .meta.model_registry import _model_registry
        _model_registry.finalize_mappings()
