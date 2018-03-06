from flask_sqlalchemy_bundle import db


class OneBasic(db.PrimaryKeyModel):
    class Meta:
        lazy_mapping = True

    name = db.Column(db.String)


class OneParent(db.PrimaryKeyModel):
    class Meta:
        lazy_mapping = True
        relationships = {'OneChild': 'children'}

    name = db.Column(db.String)

    children = db.relationship('OneChild', back_populates='parent')


class OneChild(db.PrimaryKeyModel):
    class Meta:
        lazy_mapping = True
        relationships = {'OneParent': 'parent'}

    name = db.Column(db.String)

    parent_id = db.foreign_key('OneParent')
    parent = db.relationship('OneParent', back_populates='children')


class OneUserRole(db.Model):
    """Join table between User and Role"""
    class Meta:
        lazy_mapping = True
        relationships = {'OneUser': 'user',
                         'OneRole': 'role'}

    user_id = db.foreign_key('OneUser', primary_key=True)
    user = db.relationship('OneUser', back_populates='user_roles')

    role_id = db.foreign_key('OneRole', primary_key=True)
    role = db.relationship('OneRole', back_populates='role_users')

    __repr_props__ = ('user_id', 'role_id')

    def __init__(self, user=None, role=None, **kwargs):
        super().__init__(**kwargs)
        if user:
            self.user = user
        if role:
            self.role = role


class OneUser(db.PrimaryKeyModel):
    class Meta:
        lazy_mapping = True
        relationships = {'OneUserRole': 'user_roles'}

    name = db.Column(db.String)

    user_roles = db.relationship('OneUserRole', back_populates='user',
                                 cascade='all, delete-orphan')
    roles = db.association_proxy('user_roles', 'role',
                                 creator=lambda role: OneUserRole(role=role))


class OneRole(db.PrimaryKeyModel):
    class Meta:
        lazy_mapping = True
        relationships = {'OneUserRole': 'role_users'}

    name = db.Column(db.String(63), unique=True, index=True)

    role_users = db.relationship('OneUserRole', back_populates='role',
                                 cascade='all, delete-orphan')
    users = db.association_proxy('role_users', 'user',
                                 creator=lambda user: OneUserRole(user=user))

    __repr_props__ = ('id', 'name')