# import flask_sqlalchemy_bundle into generated migrations when needed
# http://alembic.zzzcomputing.com/en/latest/autogenerate.html#affecting-the-rendering-of-types-themselves
def render_migration_item(type_, obj, autogen_context):
    if 'flask_sqlalchemy_bundle' in obj.__module__:
        autogen_context.imports.add('import flask_sqlalchemy_bundle')
    return False


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # :memory:

    ALEMBIC_CONTEXT = {
        'render_item': render_migration_item,
        'template_args': {'migration_variables': []},
    }

class DevConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    pass


class StagingConfig(ProdConfig):
    pass


class TestConfig(BaseConfig):
    pass
