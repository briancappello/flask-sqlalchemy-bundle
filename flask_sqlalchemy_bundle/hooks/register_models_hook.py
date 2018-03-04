import inspect

from flask import Flask
from flask_unchained import AppFactoryHook
from typing import *

from ..extensions import db


class RegisterModelsHook(AppFactoryHook):
    name = 'models'
    priority = 10
    bundle_module_name = 'models'

    _limit_discovery_to_bundle_superclasses = True
    _limit_discovery_to_local_declarations = False

    def process_objects(self, app: Flask, models: Dict[str, Type[db.BaseModel]]):
        self.store.models = models

    def type_check(self, obj: Any) -> bool:
        if not inspect.isclass(obj):
            return False
        return issubclass(obj, db.BaseModel) and obj not in {
            db.BaseModel,
            db.Model,
            db.PrimaryKeyModel,
            db.MaterializedView,
        }

    def update_shell_context(self, ctx: dict):
        ctx.update(self.store.models)
