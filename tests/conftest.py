import pytest

import flask_sqlalchemy_bundle
from flask_sqlalchemy_bundle.extensions import SQLAlchemy
from flask_sqlalchemy_bundle.sqla.metaclass import _model_registry
from flask_unchained import AppFactory, TEST, unchained
from sqlalchemy import MetaData


# reset the Flask-SQLAlchemy extension and the _model_registry to clean slate
@pytest.fixture(autouse=True)
def db_ext():
    db = SQLAlchemy(metadata=MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    }))
    setattr(flask_sqlalchemy_bundle, 'db', db)
    _model_registry._reset()
    yield db


@pytest.fixture(autouse=True)
def app():
    unchained._initialized = False  # reset the unchained extension
    app = AppFactory.create_app('tests._app', TEST)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture(autouse=True)
def db(db_ext):
    db_ext.create_all()
    yield db_ext
    db_ext.drop_all()


@pytest.fixture(autouse=True)
def db_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    session = db.create_scoped_session(options=dict(bind=connection, binds={}))
    db.session = session

    try:
        yield session
    finally:
        transaction.rollback()
        connection.close()
        session.remove()
