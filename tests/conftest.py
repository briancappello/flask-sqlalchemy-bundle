import importlib
import pytest

from flask_sqlalchemy_bundle.sqla.metaclass import _model_registry
from flask_unchained import AppFactory, TEST, unchained
from sqlalchemy import MetaData


# reset the Flask-SQLAlchemy extension and the _model_registry to clean slate
# support loading the extension from different test bundles.
# NOTE: luckily none of these hacks are required in end users' test suites
# making use of flask_sqlalchemy_bundle
@pytest.fixture(autouse=True)
def db_ext(bundles):
    db_bundles = ['flask_sqlalchemy_bundle', 'tests._bundles.custom_extension']
    try:
        module_name = [m for m in db_bundles if m in bundles][0]
    except (IndexError, TypeError):
        module_name = 'flask_sqlalchemy_bundle'
    extensions_module_name = f'{module_name}.extensions'

    _model_registry._reset()

    db_module = importlib.import_module(module_name)
    db_extensions_module = importlib.import_module(extensions_module_name)

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


@pytest.fixture()
def bundles(request):
    return getattr(request.keywords.get('bundles'), 'args', [None])[0]


@pytest.fixture(autouse=True)
def app(bundles, db_ext):
    if (bundles and 'tests._bundles.custom_extension' not in bundles
            and 'flask_sqlalchemy_bundle' not in bundles):
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
