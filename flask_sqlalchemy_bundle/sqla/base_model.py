from flask_sqlalchemy.model import Model as FlaskSQLAlchemyBaseModel
from flask_unchained import pluralize, title_case
from sqlalchemy.ext.declarative import declared_attr

from .meta import ModelMetaFactory


class BaseModel(FlaskSQLAlchemyBaseModel):
    """Base table class. It includes convenience methods for creating,
    querying, saving, updating and deleting models.
    """
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    _meta_factory_class = ModelMetaFactory

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


# this base class is unused by default, but end users choose to use it
class QueryBaseModel(BaseModel):
    @classmethod
    def all(cls):
        """Get all models."""
        return cls.query.all()

    @classmethod
    def get(cls, id):
        """Get one model by ID.

        :param id: The model ID to get.
        """
        return cls.query.get(int(id))

    @classmethod
    def get_by(cls, **kwargs):
        """Get one model by keyword arguments.

        :param kwargs: The model attribute values to filter by.
        """
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def join(cls, *props, **kwargs):
        return cls.query.join(*props, **kwargs)

    @classmethod
    def filter(cls, *args, **kwargs):
        return cls.query.filter(*args, **kwargs)

    @classmethod
    def filter_by(cls, **kwargs):
        """Find models by keyword arguments.

        :param kwargs: The model attribute values to filter by.
        """
        return cls.query.filter_by(**kwargs)
