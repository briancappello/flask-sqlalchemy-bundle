from flask_sqlalchemy_bundle import db


class OneRelationship(db.Model):
    class Meta:
        lazy_mapping = True

    name = db.Column(db.String)
    backrefs = db.relationship('OneBackref', backref=db.backref('relationship'))


class OneBackref(db.Model):
    class Meta:
        lazy_mapping = True

    name = db.Column(db.String)
    relationship_id = db.foreign_key('OneRelationship')
