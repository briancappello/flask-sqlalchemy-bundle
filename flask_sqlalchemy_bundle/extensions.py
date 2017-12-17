from flask_alembic import Alembic
from sqlalchemy import MetaData

from .sqla_extension import SQLAlchemy


alembic = Alembic(
    command_name=None,  # use AppFactory to register the commands instead
)

db = SQLAlchemy(metadata=MetaData(naming_convention={
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}))


EXTENSIONS = {
    'db': db,
    'alembic': (alembic, ['db']),
}
