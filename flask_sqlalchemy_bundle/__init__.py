from flask_application_factory import Bundle

from .extensions import db
from .register_models_hook import RegisterModelsHook


class FlaskSQLAlchemyBundle(Bundle):
    module_name = __name__
    name = 'db'
    hooks = [RegisterModelsHook]
