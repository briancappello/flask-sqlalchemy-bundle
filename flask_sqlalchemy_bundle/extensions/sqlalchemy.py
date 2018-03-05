from functools import partial
from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy, BaseQuery
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from .. import sqla
from ..sqla import BaseModel
from ..sqla.metaclass import SQLAlchemyBaseModelMeta


class SQLAlchemy(BaseSQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=BaseQuery, model_class=BaseModel):
        super().__init__(app, use_native_unicode, session_options,
                         metadata, query_class, model_class)
        self.BaseModel = self.make_declarative_base(BaseModel, metadata)

        class Model(sqla.TimestampMixin, self.BaseModel):
            __abstract__ = True
            __repr_props__ = ('created_at', 'updated_at')
        self.Model = Model

        class PrimaryKeyModel(sqla.PrimaryKeyMixin, self.Model):
            __abstract__ = True
            __repr_props__ = ('id', 'created_at', 'updated_at')
        self.PrimaryKeyModel = PrimaryKeyModel

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
        self.include_polymorphic_model()

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

        class MaterializedView(self.BaseModel):
            __abstract__ = True

            @sqla.declared_attr
            def __tablename__(self):
                return self.__table__.fullname

            @classmethod
            def refresh(cls, concurrently=True):
                self.refresh_materialized_view(cls.__tablename__, concurrently)

        self.MaterializedView = MaterializedView

    def include_polymorphic_model(self):
        class PolymorphicMeta(SQLAlchemyBaseModelMeta):
            def __new__(mcs, name, bases, clsdict):
                if '__abstract__' in clsdict:
                    return super().__new__(mcs, name, bases, clsdict)

                # automatically configure mapper_args
                mapper_args = clsdict.get('__mapper_args__', {})
                if bases[0] in {PolymorphicModel}:
                    mapper_args['polymorphic_on'] = \
                        PolymorphicModel.discriminator
                if 'polymorphic_identity' not in mapper_args:
                    mapper_args['polymorphic_identity'] = name

                clsdict['__mapper_args__'] = mapper_args
                return super().__new__(mcs, name, bases, clsdict)

        class PolymorphicModel(self.PrimaryKeyModel, metaclass=PolymorphicMeta):
            __abstract__ = True
            discriminator = self.Column(self.String(64))
        self.PolymorphicModel = PolymorphicModel

    def make_declarative_base(self, model, metadata=None) -> BaseModel:
        if not isinstance(model, DeclarativeMeta):
            def abstract_model_meta(name, bases, clsdict):
                clsdict['__abstract__'] = True
                return SQLAlchemyBaseModelMeta(name, bases, clsdict)

            model = declarative_base(
                cls=model,
                name='BaseModel',
                metadata=metadata,
                metaclass=abstract_model_meta,
            )
        return super().make_declarative_base(model, metadata)
