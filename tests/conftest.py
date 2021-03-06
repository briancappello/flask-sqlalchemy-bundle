import importlib
import os
import pytest
import sys

from flask_sqlalchemy_bundle.meta.model_registry import _model_registry
from flask_unchained import AppFactory, TEST, unchained
from sqlalchemy import MetaData
from sqlalchemy.orm import clear_mappers

PRIOR_FLASK_ENV = os.getenv('FLASK_ENV', None)

POSTGRES = '{dialect}://{user}:{password}@{host}:{port}/{db_name}'.format(
    dialect='postgresql+psycopg2',
    user='flask_test',
    password='flask_test',
    host='127.0.0.1',
    port=5432,
    db_name='flask_test')


@pytest.fixture()
def bundles(request):
    try:
        return request.keywords.get('bundles').args[0]
    except AttributeError:
        return ['flask_sqlalchemy_bundle']


# reset the Flask-SQLAlchemy extension and the _model_registry to clean slate,
# support loading the extension from different test bundles.
# NOTE: luckily none of these hacks are required in end users' test suites that
# make use of flask_sqlalchemy_bundle
@pytest.fixture(autouse=True)
def db_ext(bundles):
    os.environ['FLASK_ENV'] = TEST

    sqla_bundle = 'flask_sqlalchemy_bundle'
    db_bundles = [sqla_bundle, 'tests._bundles.custom_extension']
    try:
        bundle_under_test = [m for m in db_bundles if m in bundles][0]
    except (IndexError, TypeError):
        bundle_under_test = sqla_bundle

    _model_registry._reset()
    unchained._reset()
    clear_mappers()

    # NOTE: this logic is only correct for one level deep of bundle extension
    # (the proper behavior from unchained hooks is to import the full
    # inheritance hierarchy, and that is especially essential for all of the
    # metaclass magic in this bundle to work correctly)
    modules_to_import = ([bundle_under_test] if bundle_under_test == sqla_bundle
                         else [sqla_bundle, bundle_under_test])

    for module_name in modules_to_import:
        if module_name in sys.modules:
            del sys.modules[module_name]
        db_module = importlib.import_module(module_name)

        ext_module_name = f'{module_name}.extensions'
        if ext_module_name in sys.modules:
            del sys.modules[ext_module_name]
        db_extensions_module = importlib.import_module(ext_module_name)

    kwargs = getattr(db_extensions_module, 'kwargs', dict(
        metadata=MetaData(naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        }),
    ))

    db = db_extensions_module.SQLAlchemy(**kwargs)
    unchained.extensions.db = db

    for module in [db_module, db_extensions_module]:
        setattr(module, 'db', db)

    EXTENSIONS = getattr(db_extensions_module, 'EXTENSIONS')
    EXTENSIONS['db'] = db
    setattr(db_extensions_module, 'EXTENSIONS', EXTENSIONS)

    yield db


@pytest.fixture(autouse=True)
def app(bundles, db_ext):
    if (bundles and 'tests._bundles.custom_extension' not in bundles
            and 'flask_sqlalchemy_bundle' not in bundles):
        bundles.insert(0, 'flask_sqlalchemy_bundle')

    unchained._reset()
    app = AppFactory.create_app(TEST, bundles=bundles)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

    if PRIOR_FLASK_ENV:
        os.environ['FLASK_ENV'] = PRIOR_FLASK_ENV
    else:
        del os.environ['FLASK_ENV']


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
