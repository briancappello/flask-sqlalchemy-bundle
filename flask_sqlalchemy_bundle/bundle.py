import os

from flask import Flask
from flask_application_factory import Bundle
from typing import List

from .sqla.model import BaseModel


class FlaskSQLAlchemyBundle(Bundle):
    module_name = __name__
    command_group_names = ['db']
    model_base_classes = [BaseModel]

    def pre_configure_app(self, app: Flask, config_class, bundles: List[Bundle]):
        super().pre_configure_app(app, config_class, bundles)

        alembic = getattr(config_class, 'ALEMBIC', {})
        if not alembic.get('script_location', None):
            alembic['script_location'] = os.path.join(
                config_class.PROJECT_ROOT, 'migrations')
            setattr(config_class, 'ALEMBIC', alembic)

    def post_register_extensions(self, app: Flask, bundles: List[Bundle]):
        super().post_register_extensions(app, bundles)

        # auto-register migration branch names/locations
        #
        # even though this is a configuration setting, it must come after
        # extensions have been registered because some third party extensions
        # dynamically create models upon init_app (which hasn't been called
        # yet at pre/post_configure_app, so the models don't exist until now)
        alembic = app.config.get('ALEMBIC', {})
        if not alembic.get('version_locations', None):
            alembic['version_locations'] = [
                (bundle.name, os.path.join(bundle.root_dir, 'migrations'))
                for bundle in bundles if bundle.get_models()]
            app.config.from_mapping({'ALEMBIC': alembic})
