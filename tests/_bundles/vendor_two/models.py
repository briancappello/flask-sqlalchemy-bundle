from flask_sqlalchemy_bundle import db


class TwoBasic(db.Model):
    class Meta:
        lazy_mapped = True

    name = db.Column(db.String, index=True)
