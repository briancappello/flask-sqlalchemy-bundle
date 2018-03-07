from flask_sqlalchemy_bundle import db


class Person(db.Model):
    class Meta:
        polymorphic = True

    name = db.Column(db.String)


class Employee(Person):
    company = db.Column(db.String)
