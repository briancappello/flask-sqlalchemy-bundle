import pytest

import flask_sqlalchemy_bundle
from flask_sqlalchemy_bundle.extensions import SQLAlchemy
from flask_sqlalchemy_bundle.sqla.metaclass import _model_registry
from flask_unchained import AppFactory, TEST, unchained
from sqlalchemy import MetaData


# reset the Flask-SQLAlchemy extension and the _model_registry to clean slate
@pytest.fixture(autouse=True)
def db_ext():
    _model_registry._reset()
    db = SQLAlchemy(metadata=MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    }))
    setattr(flask_sqlalchemy_bundle, 'db', db)
    yield db


@pytest.fixture()
def bundles(request):
    return getattr(request.keywords.get('bundles'), 'args', [None])[0]


@pytest.fixture(autouse=True)
def app(bundles, db_ext):
    if bundles and 'flask_sqlalchemy_bundle' not in bundles:
        bundles.insert(0, 'flask_sqlalchemy_bundle')
    unchained._initialized = False  # reset the unchained extension
    app = AppFactory.create_app('tests._app', TEST, bundles=bundles)
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
