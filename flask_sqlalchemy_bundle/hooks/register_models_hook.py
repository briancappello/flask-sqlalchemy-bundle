import inspect
import sys

from flask import Flask
from flask_unchained import AppFactoryHook
from typing import *

from ..extensions import db
from ..sqla.metaclass import _model_registry


class RegisterModelsHook(AppFactoryHook):
    name = 'models'
    priority = 10
    bundle_module_name = 'models'

    def process_objects(self, app: Flask, all_discovered_models):
        # this hook is responsible for discovering models, which happens by
        # importing each bundle's models module. the metaclasses of models
        # register themselves with the model registry. and the model registry
        # has final say over which models should end up getting mapped with
        # SQLAlchemy
        self.store.models = _model_registry.finalize_mappings()

    def type_check(self, obj: Any) -> bool:
        if not inspect.isclass(obj):
            return False
        return issubclass(obj, db.BaseModel) and obj not in {
            db.BaseModel,
            db.Model,
            db.PrimaryKeyModel,
            db.MaterializedView,
            db.PolymorphicModel,
        }

    def update_shell_context(self, ctx: dict):
        ctx.update(self.store.models)

    def import_bundle_module(self, bundle):
        module_name = self.get_module_name(bundle)
        testing = getattr(self.unchained.app_config_cls, 'TESTING', False)
        if testing and module_name in sys.modules:
            del sys.modules[module_name]
        return super().import_bundle_module(bundle)
