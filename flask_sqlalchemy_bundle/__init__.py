from flask_unchained import Bundle

from .alembic import MaterializedViewMigration
from .decorators import param_converter
from .extensions import db
from .services import ModelManager, SessionManager


class FlaskSQLAlchemyBundle(Bundle):
    name = 'flask_sqlalchemy_bundle'
    command_group_names = ['db']
