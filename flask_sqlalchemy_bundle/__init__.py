from flask_unchained import Bundle

from .decorators import param_converter
from .extensions import db
from .register_models_hook import RegisterModelsHook
from .sqlalchemy_bundle_store import SQLAlchemyBundleStore


class FlaskSQLAlchemyBundle(Bundle):
    name = 'db'
    hooks = [RegisterModelsHook]
    store = SQLAlchemyBundleStore()
