import inspect

from flask_sqlalchemy.model import Model, camel_to_snake_case
from sqlalchemy.schema import ForeignKey

from .column import Column
from .types import BigInteger


# RELATIONSHIP DOCS
# http://docs.sqlalchemy.org/en/rel_1_1/orm/basic_relationships.html#relationship-patterns
# http://docs.sqlalchemy.org/en/rel_1_1/orm/backref.html#relationships-backref
# http://flask-sqlalchemy.pocoo.org/2.2/models/#one-to-many-relationships
# http://flask-sqlalchemy.pocoo.org/2.2/models/#many-to-many-relationships


def foreign_key(model_or_table_name, fk_col=None, primary_key=False, **kwargs):
    """Helper method to add a foreign key Column to a model.

    For example::

        class Post(Model):
            category_id = foreign_key('Category')
            category = relationship('Category', back_populates='posts')

    Is equivalent to::

        class Post(Model):
            category_id = Column(BigInteger, ForeignKey('category.id'), nullable=False)
            category = relationship('Category', back_populates='posts')

    :param model_or_table_name: the model or table name to link to

        If given a lowercase string, it's treated as an explicit table name.

        If there are any uppercase characters, it's assumed to be a model name,
        and will be converted to snake case using the same automatic conversion
        as Flask-SQLAlchemy does itself.

        If given a subclass of :class:`flask_sqlalchemy.Model`, use its
        :attr:`__tablename__` attribute.

    :param str fk_col: column name of the primary key (defaults to "id")
    :param bool primary_key: Whether or not this Column is a primary key
    :param dict kwargs: any other kwargs to pass the Column constructor
    """
    fk_col = fk_col or 'id'
    table_name = model_or_table_name
    model = model_or_table_name
    if inspect.isclass(model) and issubclass(model, Model):
        table_name = model.__tablename__
    elif table_name != model_or_table_name.lower():
        table_name = camel_to_snake_case(model_or_table_name)
    return Column(BigInteger, ForeignKey(f'{table_name}.{fk_col}'),
                  primary_key=primary_key, **kwargs)
