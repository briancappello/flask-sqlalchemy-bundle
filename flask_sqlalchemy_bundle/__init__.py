from flask_unchained import Bundle

from .alembic import MaterializedViewMigration
from .decorators import param_converter
from .extensions import db
from .register_models_hook import RegisterModelsHook
from .sqlalchemy_bundle_store import SQLAlchemyBundleStore


class FlaskSQLAlchemyBundle(Bundle):
    name = 'flask_sqlalchemy_bundle'
    command_group_names = ['db']
    hooks = [RegisterModelsHook]
    store = SQLAlchemyBundleStore
