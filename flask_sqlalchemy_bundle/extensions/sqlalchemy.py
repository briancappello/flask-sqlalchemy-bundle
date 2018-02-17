from functools import partial
from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy, BaseQuery

from .. import sqla


class SQLAlchemy(BaseSQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=BaseQuery, model_class=sqla.BaseModel):
        super().__init__(app, use_native_unicode, session_options,
                         metadata, query_class, model_class)

        self._BaseModel = self.make_declarative_base(sqla.BaseModel, metadata)
        self.PrimaryKeyMixin = sqla.PrimaryKeyMixin
        self.TimestampMixin = sqla.TimestampMixin

        class BaseModel(self.TimestampMixin, self._BaseModel):
            __abstract__ = True
            __table_args__ = {'extend_existing': True}
            __repr_props__ = ('created_at', 'updated_at')
        self.BaseModel = BaseModel

        class Model(self.PrimaryKeyMixin, self.BaseModel):
            __abstract__ = True
            __table_args__ = {'extend_existing': True}
            __repr_props__ = ('id', 'created_at', 'updated_at')
        self.Model = Model

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

        class MaterializedView(self._BaseModel):
            __abstract__ = True

            @sqla.declared_attr
            def __tablename__(self):
                return self.__table__.fullname

            @classmethod
            def refresh(cls, concurrently=True):
                self.refresh_materialized_view(cls.__tablename__, concurrently)

        self.MaterializedView = MaterializedView
