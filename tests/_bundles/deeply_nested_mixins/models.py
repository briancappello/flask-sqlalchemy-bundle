from flask_sqlalchemy_bundle import db


class B1(db.PrimaryKeyModel):
    pass


class B2(db.PrimaryKeyModel):
    pass


class B3(B1, B2):
    pass


class B4(db.PrimaryKeyModel):
    pass


class B5(B4, B3):
    pass


class B6(db.PrimaryKeyModel):
    pass


class GenericMixin:
    pass


class B7(B5, B6, GenericMixin):
    pass