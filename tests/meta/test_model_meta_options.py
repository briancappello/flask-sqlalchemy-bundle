import pytest

from flask_sqlalchemy_bundle.meta.model_registry import _model_registry
from tests.conftest import POSTGRES


class TestModelMetaOptions:
    def test_defaults(self, db):
        meta = db.Model._meta
        assert meta._testing_ == 'this setting is only available when ' \
                                 'os.getenv("FLASK_ENV") == "test"'

        assert meta.abstract is True
        assert meta.lazy_mapped is False
        assert meta.relationships is None

        assert meta._base_tablename is None
        assert meta.polymorphic is False
        assert meta.polymorphic_on is None
        assert meta.polymorphic_identity is None

        assert meta.pk == 'id'
        assert meta.created_at == 'created_at'
        assert meta.updated_at == 'updated_at'

    def test_overriding_defaults_with_inheritance(self, db):
        class Over(db.Model):
            class Meta:
                lazy_mapped = True
                relationships = {}
                pk = 'pk'
                created_at = 'created'
                updated_at = 'updated'
                _testing_ = 'over'

        meta = Over._meta
        assert meta._testing_ == 'over'
        assert meta.abstract is False
        assert meta.lazy_mapped is True
        assert meta.relationships == {}

        assert meta._base_tablename is None
        assert meta.polymorphic is False
        assert meta.polymorphic_on is None
        assert meta.polymorphic_identity is None

        assert meta.pk == 'pk'
        assert meta.created_at == 'created'
        assert meta.updated_at == 'updated'

        class ExtendsOver(Over):
            class Meta:
                updated_at = 'extends'

        meta = ExtendsOver._meta
        assert meta._testing_ == 'over'
        assert meta.abstract is False
        assert meta.lazy_mapped is True
        assert meta.relationships == {}

        assert meta._base_tablename == 'over'
        assert meta.polymorphic is False
        assert meta.polymorphic_on is None
        assert meta.polymorphic_identity is None

        assert meta.pk == 'pk'
        assert meta.created_at == 'created'
        assert meta.updated_at == 'extends'

    @pytest.mark.options(SQLALCHEMY_DATABASE_URI=POSTGRES)
    def test_tablename(self, db):
        class NotLazy(db.Model):
            class Meta:
                abstract = True
                lazy_mapped = False

        class Auto(NotLazy):
            pass

        assert Auto._meta.table is None
        assert '__tablename__' not in Auto._meta._mcs_args.clsdict
        assert Auto.__tablename__ == 'auto'

        class DeclaredAttr(NotLazy):
            @db.declared_attr
            def __tablename__(cls):
                return cls.__name__.lower()

        assert DeclaredAttr._meta.table is None
        assert DeclaredAttr.__tablename__ == 'declaredattr'

        class Manual(NotLazy):
            __tablename__ = 'manuals'

        assert Manual._meta.table == 'manuals'
        assert Manual._meta._mcs_args.clsdict['__tablename__'] == 'manuals'
        assert Manual.__tablename__ == 'manuals'

        class AutoMV(db.MaterializedView):
            @classmethod
            def selectable(cls):
                return db.select([Auto.id])

        _model_registry.finalize_mappings()

        assert AutoMV._meta.table == 'autoMV'
        assert AutoMV.__table__.fullname == 'autoMV'
        assert AutoMV._meta._mcs_args.clsdict['__tablename__'] == 'autoMV'
        assert AutoMV.__tablename__ == 'autoMV'

        class ManualMV(db.MaterializedView):
            class Meta:
                table = 'manual_materialized_view'

            @classmethod
            def selectable(cls):
                return db.select([Manual.id])

        _model_registry.finalize_mappings()

        assert ManualMV._meta.table == 'manual_materialized_view'
        assert ManualMV.__table__.fullname == 'manual_materialized_view'
        assert ManualMV._meta._mcs_args.clsdict['__tablename__'] == \
               'manual_materialized_view'
        assert ManualMV.__tablename__ == 'manual_materialized_view'
