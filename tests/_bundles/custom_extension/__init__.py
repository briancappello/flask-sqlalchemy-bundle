from flask_sqlalchemy_bundle import FlaskSQLAlchemyBundle
from flask_unchained import unchained

from .extensions import db
unchained.extensions.db = db


class CustomSQLAlchemyBundle(FlaskSQLAlchemyBundle):
    pass
