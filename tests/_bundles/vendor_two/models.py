from flask_sqlalchemy_bundle import db


class TwoBasic(db.Model):
    name = db.Column(db.String, index=True)
