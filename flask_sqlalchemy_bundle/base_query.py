from flask_sqlalchemy import BaseQuery as FlaskSQLAlchemyBaseQuery


class BaseQuery(FlaskSQLAlchemyBaseQuery):
    def get(self, id):
        return super().get(int(id))

    def get_by(self, **kwargs):
        return self.filter_by(**kwargs).first()
