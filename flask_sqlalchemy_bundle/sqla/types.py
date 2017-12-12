import pytz

from sqlalchemy import types
from sqlalchemy.dialects import sqlite


class BigInteger(types.TypeDecorator):
    impl = types.BigInteger().with_variant(sqlite.INTEGER(), 'sqlite')

    def __repr__(self):
        return 'BigInteger()'


class DateTime(types.TypeDecorator):
    impl = types.DateTime

    def __init__(self, timezone=True):
        super().__init__(timezone=True)  # force timezone always True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError('Cannot persist timezone-naive datetime')
            return value.astimezone(pytz.UTC)

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.astimezone(pytz.UTC)
