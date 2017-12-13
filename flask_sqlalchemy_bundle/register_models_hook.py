import inspect
import os

from flask import Flask
from flask_application_factory import Bundle, FactoryHook
from typing import List

from .sqla.model import BaseModel


class RegisterModelsHook(FactoryHook):
    priority = 25
    bundle_module_name = 'models'

    def __init__(self):
        self.models = {}

    def run_hook(self, app: Flask, app_config_cls, bundles: List[Bundle]):
        bundles_with_models = []
        for bundle in bundles:
            models = self.collect_from_bundle(bundle)
            if not models:
                continue

            bundles_with_models.append(bundle)
            for name, model_class in models:
                self.models[name] = model_class

        setattr(app, 'models', self.models)
        self.configure_migrations(app, bundles_with_models)

    def type_check(self, obj):
        if not inspect.isclass(obj):
            return False
        return issubclass(obj, BaseModel) and obj != BaseModel

    def register_shell_context(self, ctx: dict):
        ctx.update(self.models)

    def configure_migrations(self, app, bundles_with_models):
        alembic = app.config.get('ALEMBIC', {})

        if not alembic.get('script_location', None):
            alembic['script_location'] = os.path.join(
                app.config['PROJECT_ROOT'], 'migrations')

        if not alembic.get('version_locations', None):
            alembic['version_locations'] = [
                (bundle.name, os.path.join(bundle.root_dir, 'migrations'))
                for bundle in bundles_with_models]

        app.config.from_mapping({'ALEMBIC': alembic})
