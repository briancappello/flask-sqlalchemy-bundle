from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy, BaseQuery

from . import sqla


class SQLAlchemy(BaseSQLAlchemy):
    def __init__(self, app=None, use_native_unicode=True, session_options=None,
                 metadata=None, query_class=BaseQuery, model_class=sqla.BaseModel):
        super().__init__(app, use_native_unicode, session_options,
                         metadata, query_class, model_class)

        self.BaseModel = self.make_declarative_base(sqla.BaseModel, metadata)
        self.Model = self.make_declarative_base(sqla.Model, metadata)
        self.PrimaryKeyMixin = sqla.PrimaryKeyMixin
        self.TimestampMixin = sqla.TimestampMixin
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

        # a bit of hackery to make type-hinting in PyCharm work better
        if False:
            self.Column = sqla._column_type_hinter_
            self.backref = sqla._relationship_type_hinter_
            self.relationship = sqla._relationship_type_hinter_
