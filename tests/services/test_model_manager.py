import pytest

from flask_sqlalchemy_bundle import ModelManager, SessionManager, SQLAlchemy
from flask_sqlalchemy_bundle.meta.model_registry import _model_registry
from flask_unchained import unchained
from sqlalchemy.orm.exc import MultipleResultsFound


def setup(db: SQLAlchemy):
    class Foo(db.Model):
        name = db.Column(db.String)

    # simulate the register models hook
    unchained.flask_sqlalchemy_bundle.models['Foo'] = Foo

    class FooManager(ModelManager):
        model = 'Foo'

    _model_registry.finalize_mappings()
    db.create_all()

    session_manager = SessionManager()
    foo_manager = FooManager(session_manager)

    return Foo, foo_manager, session_manager


class TestModelManager:
    def test_it_accepts_a_model_class(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo = foo_manager.create(name='foobar')
        assert isinstance(foo, Foo)

        # check it's added to the session but not committed
        assert foo in db.session
        with db.session.no_autoflush:
            assert foo_manager.get_by(name='foobar') is None

        session_manager.commit()
        assert foo_manager.get_by(name='foobar') == foo

    def test_it_accepts_a_model_class_by_name(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo = foo_manager.create(name='foobar')
        assert isinstance(foo, Foo)

        # check it's added to the session but not committed
        assert foo in db.session
        with db.session.no_autoflush:
            assert foo_manager.get_by(name='foobar') is None

        session_manager.commit()
        assert foo_manager.get_by(name='foobar') == foo

    def test_update(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo = foo_manager.create(name='foo')
        session_manager.commit()

        foo_manager.update(foo, name='foobar')
        session_manager.commit()

        assert foo_manager.get_by(name='foobar') == foo

    def test_get(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo = foo_manager.create(name='foo')
        session_manager.commit()

        assert foo_manager.get(int(foo.id)) == foo
        assert foo_manager.get(float(foo.id)) == foo
        assert foo_manager.get(str(foo.id)) == foo

        assert foo_manager.get(42) is None

    def test_get_or_create(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo, created = foo_manager.get_or_create(name='foo')
        assert created is True
        assert foo in db.session
        with db.session.no_autoflush:
            assert foo_manager.get_by(name='foo') is None
        session_manager.commit()
        assert foo_manager.get_by(name='foo') == foo

        foo1, created = foo_manager.get_or_create(id=foo.id)
        assert created is False
        assert foo1 == foo

        foo1, created = foo_manager.get_or_create(name='foo')
        assert created is False
        assert foo1 == foo

        foo2, created = foo_manager.get_or_create(name='foobar')
        assert created is True

    def test_get_by(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo1 = foo_manager.create(name='one')
        foo_1 = foo_manager.create(name='one')
        foo2 = foo_manager.create(name='two')
        session_manager.commit()

        assert foo_manager.get_by(name='fail') is None
        with pytest.raises(MultipleResultsFound):
            foo_manager.get_by(name='one')

        assert foo_manager.get_by(name='two') == foo2

    def test_find_all(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo1 = foo_manager.create(name='one')
        foo2 = foo_manager.create(name='two')
        foo3 = foo_manager.create(name='three')
        session_manager.commit()

        all_ = [foo1, foo2, foo3]
        assert foo_manager.find_all() == all_

    def test_find_by(self, db: SQLAlchemy):
        Foo, foo_manager, session_manager = setup(db)

        foo1 = foo_manager.create(name='one')
        foo_1 = foo_manager.create(name='one')
        foo2 = foo_manager.create(name='two')
        session_manager.commit()

        ones = [foo1, foo_1]
        assert foo_manager.find_by(name='one') == ones
