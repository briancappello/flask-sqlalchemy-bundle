from flask_sqlalchemy_bundle import db


class TwoBasic(db.Model):
    app = db.Column(db.String)
