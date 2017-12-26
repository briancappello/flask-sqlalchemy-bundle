import inspect
import os

from flask import Flask
from flask_unchained import AppFactoryHook

from .sqla.model import BaseModel


class RegisterModelsHook(AppFactoryHook):
    name = 'models'
    priority = 10
    bundle_module_name = 'models'

    def process_objects(self, app: Flask, objects):
        for name, model_class in objects:
            self.store.models[name] = model_class

        self.configure_migrations(app)

    def type_check(self, obj):
        if not inspect.isclass(obj):
            return False
        return issubclass(obj, BaseModel) and obj != BaseModel

    def update_shell_context(self, ctx: dict):
        ctx.update(self.store.models)

    def configure_migrations(self, app):
        alembic = app.config.get('ALEMBIC', {})

        if not alembic.get('script_location'):
            alembic['script_location'] = os.path.join(
                app.config['PROJECT_ROOT'], 'db', 'migrations')

        app.config.from_mapping({'ALEMBIC': alembic})
