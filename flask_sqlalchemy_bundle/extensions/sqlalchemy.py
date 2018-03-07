from functools import partial
from flask_sqlalchemy import (BaseQuery, DefaultMeta,
                              SQLAlchemy as BaseSQLAlchemy)
from sqlalchemy.ext.declarative import declarative_base

from .. import sqla
from ..sqla import BaseModel
from ..sqla.metaclass import SQLAlchemyBaseModelMeta


class SQLAlchemy(BaseSQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=BaseQuery, model_class=BaseModel,
                 model_metaclass=SQLAlchemyBaseModelMeta):
        super().__init__(app, use_native_unicode=use_native_unicode,
                         session_options=session_options,
                         metadata=metadata,
                         query_class=query_class,
                         model_class=model_class)

        self.Model = self.make_declarative_base(
            model_class, metadata, model_metaclass)

        self.Column = sqla.Column
        self.BigInteger = sqla.BigInteger
        self.DateTime = sqla.DateTime

        self.association_proxy = sqla.association_proxy
        self.declared_attr = sqla.declared_attr
        self.foreign_key = sqla.foreign_key
        self.hybrid_method = sqla.hybrid_method
        self.hybrid_property = sqla.hybrid_property

        self.attach_events = sqla.attach_events
        self.on = sqla.on
        self.slugify = sqla.slugify

        self.include_materialized_view()

        # a bit of hackery to make type-hinting in PyCharm work better
        if False:
            self.Column = sqla._column_type_hinter_
            self.backref = sqla._relationship_type_hinter_
            self.relationship = sqla._relationship_type_hinter_
            self.create_materialized_view = sqla._create_materialized_view
            self.refresh_materialized_view = sqla._refresh_materialized_view
            self.refresh_all_materialized_views = sqla._refresh_all_materialized_views

    def include_materialized_view(self):
        # inject the database extension to prevent circular imports
        self.create_materialized_view = \
            partial(sqla._create_materialized_view, db=self)
        self.refresh_materialized_view = \
            partial(sqla._refresh_materialized_view, db=self)
        self.refresh_all_materialized_views = \
            partial(sqla._refresh_all_materialized_views, db=self)

        class MaterializedView(self.Model):
            __abstract__ = True

            @sqla.declared_attr
            def __tablename__(self):
                return self.__table__.fullname

            @classmethod
            def refresh(cls, concurrently=True):
                self.refresh_materialized_view(cls.__tablename__, concurrently)

        self.MaterializedView = MaterializedView

    def make_declarative_base(self, model, metadata=None,
                              metaclass=SQLAlchemyBaseModelMeta) -> BaseModel:
        if not isinstance(model, DefaultMeta):
            def make_model_metaclass(name, bases, clsdict):
                clsdict['__abstract__'] = True
                return metaclass(name, bases, clsdict)

            model = declarative_base(
                cls=model,
                name='Model',
                metadata=metadata,
                metaclass=make_model_metaclass,
            )
        return super().make_declarative_base(model, metadata)
