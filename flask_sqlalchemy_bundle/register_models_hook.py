import inspect
import os

from flask import Flask
from flask_application_factory import FactoryHook

from .sqla.model import BaseModel


class RegisterModelsHook(FactoryHook):
    priority = 25
    bundle_module_name = 'models'
    models = {}

    def process_objects(self, app: Flask, app_config_cls, objects):
        for name, model_class in objects:
            self.models[name] = model_class

        setattr(app, 'models', self.models)
        self.configure_migrations(app)

    def type_check(self, obj):
        if not inspect.isclass(obj):
            return False
        return issubclass(obj, BaseModel) and obj != BaseModel

    def register_shell_context(self, ctx: dict):
        ctx.update(self.models)

    def configure_migrations(self, app):
        alembic = app.config.get('ALEMBIC', {})

        if not alembic.get('script_location'):
            alembic['script_location'] = os.path.join(
                app.config['PROJECT_ROOT'], 'db', 'migrations')

        app.config.from_mapping({'ALEMBIC': alembic})
