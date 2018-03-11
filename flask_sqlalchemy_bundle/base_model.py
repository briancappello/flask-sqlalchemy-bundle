from flask_sqlalchemy.model import Model as FlaskSQLAlchemyBaseModel
from flask_unchained.string_utils import pluralize, title_case
from sqlalchemy.ext.declarative import declared_attr

from .meta import ModelMetaFactory


class QueryAliasDescriptor:
    def __get__(self, instance, cls):
        return cls.query


class BaseModel(FlaskSQLAlchemyBaseModel):
    """Base table class. It includes convenience methods for creating,
    querying, saving, updating and deleting models.
    """
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    class Meta:
        pk = 'id'
        created_at = 'created_at'
        updated_at = 'updated_at'
        polymorphic = False

        # this is strictly for testing meta class stuffs
        _testing_ = 'this setting is only available when ' \
                    'os.getenv("FLASK_ENV") == "test"'

    _meta_factory_class = ModelMetaFactory

    q = QueryAliasDescriptor()

    __repr_props__ = ()
    """Set to customize automatic string representation.

    For example::

        class User(database.Model):
            __repr_props__ = ('id', 'email')

            email = Column(String)

        user = User(id=1, email='foo@bar.com')
        print(user)  # prints <User id=1 email="foo@bar.com">
    """

    def __repr__(self):
        properties = [f'{prop}={getattr(self, prop)!r}'
                      for prop in self.__repr_props__ if hasattr(self, prop)]
        return f"<{self.__class__.__name__} {' '.join(properties)}>"

    @declared_attr
    def __plural__(self):
        return pluralize(self.__name__)

    @declared_attr
    def __label__(self):
        return title_case(self.__name__)

    @declared_attr
    def __plural_label__(self):
        return title_case(pluralize(self.__name__))

    def update(self, **kwargs):
        """Update fields on the model.

        :param kwargs: The model attribute values to update the model with.
        """
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return self
