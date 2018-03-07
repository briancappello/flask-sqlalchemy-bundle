from flask_sqlalchemy import (BaseQuery, DefaultMeta,
                              SQLAlchemy as BaseSQLAlchemy)
from sqlalchemy.ext.declarative import declarative_base

from .. import sqla
from ..sqla import BaseModel
from ..sqla.metaclass import SQLAlchemyBaseModelMeta, _model_registry


class SQLAlchemy(BaseSQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=BaseQuery, model_class=BaseModel):
        super().__init__(app, use_native_unicode=use_native_unicode,
                         session_options=session_options,
                         metadata=metadata,
                         query_class=query_class,
                         model_class=model_class)
        _model_registry.register_base_model_class(self.Model)

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

        self.create_materialized_view = sqla.create_materialized_view
        self.refresh_materialized_view = sqla.refresh_materialized_view
        self.refresh_all_materialized_views = sqla.refresh_all_materialized_views

        class MaterializedView(self.Model):
            class Meta:
                abstract = True
                pk = None
                created_at = None
                updated_at = None

            @sqla.declared_attr
            def __tablename__(self):
                return self.__table__.fullname

            @classmethod
            def refresh(cls, concurrently=True):
                sqla.refresh_materialized_view(cls.__tablename__, concurrently)

        self.MaterializedView = MaterializedView

        # a bit of hackery to make type-hinting in PyCharm work better
        if False:
            self.Column = sqla._column_type_hinter_
            self.backref = sqla._relationship_type_hinter_
            self.relationship = sqla._relationship_type_hinter_

    def make_declarative_base(self, model, metadata=None) -> BaseModel:
        if not isinstance(model, DefaultMeta):
            def make_model_metaclass(name, bases, clsdict):
                clsdict['__abstract__'] = True
                clsdict['__module__'] = model.__module__
                return SQLAlchemyBaseModelMeta(name, bases, clsdict)

            model = declarative_base(
                cls=model,
                name='Model',
                metadata=metadata,
                metaclass=make_model_metaclass,
            )
        return super().make_declarative_base(model, metadata)
