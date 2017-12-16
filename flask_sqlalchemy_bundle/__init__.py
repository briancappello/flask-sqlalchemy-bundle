from flask_unchained import Bundle

from .extensions import db
from .register_models_hook import RegisterModelsHook


class FlaskSQLAlchemyBundle(Bundle):
    name = 'db'
    hooks = [RegisterModelsHook]
