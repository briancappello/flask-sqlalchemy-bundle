from flask_sqlalchemy_bundle import db


class TwoBasic(db.PrimaryKeyModel):
    name = db.Column(db.String)
