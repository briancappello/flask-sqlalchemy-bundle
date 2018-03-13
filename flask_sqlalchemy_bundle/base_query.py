from flask_sqlalchemy import BaseQuery as FlaskSQLAlchemyBaseQuery
from sqlalchemy.orm.exc import NoResultFound


class BaseQuery(FlaskSQLAlchemyBaseQuery):
    def get(self, id):
        return super().get(int(id))

    def get_by(self, **kwargs):
        try:
            return self.filter_by(**kwargs).one()
        except NoResultFound:
            return None
