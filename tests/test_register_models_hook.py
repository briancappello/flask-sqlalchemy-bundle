import pytest
from typing import *

from flask_unchained import unchained

from flask_sqlalchemy_bundle import db
from flask_sqlalchemy_bundle.hooks import RegisterModelsHook, Store

from ._bundles.backref import BackrefBundle
from ._bundles.vendor_one import VendorOneBundle
from ._bundles.ext_vendor_one import ExtVendorOneBundle
from ._bundles.ext_ext_vendor_one import ExtExtVendorOneBundle
from ._bundles.vendor_two import VendorTwoBundle


@pytest.fixture()
def hook():
    store = Store()
    return RegisterModelsHook(unchained, store)


def _to_dict(models: List[Type[db.BaseModel]]) -> Dict[str, Type[db.BaseModel]]:
    return {model.__name__: model for model in models}


def _to_metadata_tables(models: Dict[str, Type[db.BaseModel]]):
    return {model.__tablename__: model.__table__ for model in models.values()}


def get_vendor_one_models():
    from ._bundles.vendor_one.models import (
        OneBasic,
        OneParent, OneChild,
        OneUserRole, OneUser, OneRole)
    return _to_dict([OneBasic,
                     OneParent, OneChild,
                     OneUserRole, OneUser, OneRole])


def get_vendor_two_models():
    from ._bundles.vendor_two.models import TwoBasic
    return _to_dict([TwoBasic])


def get_ext_vendor_one_models():
    from ._bundles.ext_vendor_one.models import (
        OneBasic, OneParent, OneUser, OneRole)
    d = {**get_vendor_one_models(), **_to_dict([OneBasic, OneParent,
                                                OneUser, OneRole])}
    # overridden OneParent has no children relationship, make sure the
    # OneChild model does not end up getting mapped
    d.pop('OneChild')

    # The overridden OneUser and OneRole classes have changed the roles
    # relationship to be one-to-many instead of many-to-many. make sure the
    # many-to-many join table does not end up getting mapped
    d.pop('OneUserRole')
    return d


def get_ext_ext_vendor_one_models():
    from ._bundles.vendor_one.models import OneUserRole
    from ._bundles.ext_ext_vendor_one.models import OneUser, OneRole
    return {**get_ext_vendor_one_models(),
            **_to_dict([OneRole, OneUser, OneUserRole])}


class TestRegisterModelsHookTypeCheck:
    def test_type_check_on_garbage(self, hook: RegisterModelsHook):
        assert hook.type_check('foo') is False
        assert hook.type_check(42) is False
        assert hook.type_check(42.0) is False
        assert hook.type_check(None) is False
        assert hook.type_check(lambda x: x) is False
        assert hook.type_check(db) is False
        assert hook.type_check(VendorOneBundle) is False

    def test_type_check__base_model(self, hook: RegisterModelsHook):
        class BM(db.BaseModel):
            id = db.Column(db.Integer, primary_key=True)
        assert hook.type_check(db.BaseModel) is False
        assert hook.type_check(BM)

    def test_type_check_base_model(self, hook: RegisterModelsHook):
        class M(db.Model):
            id = db.Column(db.Integer, primary_key=True)
        assert hook.type_check(db.Model) is False
        assert hook.type_check(M)

    def test_type_check_model(self, hook: RegisterModelsHook):
        class PKM(db.PrimaryKeyModel):
            pass
        assert hook.type_check(db.PrimaryKeyModel) is False
        assert hook.type_check(PKM)

    # FIXME: requires PostgreSQL
    # def test_type_check_materialized_view(self, hook: RegisterModelsHook):
    #     class MVT(db.PrimaryKeyModel):
    #         name = db.Column(db.Integer, primary_key=True)
    #
    #     class MV(db.MaterializedView):
    #         __table__ = db.create_materialized_view('mv', db.select([MVT.id]))
    #
    #     assert hook.type_check(db.MaterializedView) is False
    #     assert hook.type_check(MV)

    def test_type_check_polymorphic_model(self, hook: RegisterModelsHook):
        class PM(db.PolymorphicModel):
            pass

        class PME(PM):
            id = db.foreign_key('PM', primary_key=True)
            extra = db.Column(db.String)

        assert hook.type_check(db.PolymorphicModel) is False
        assert hook.type_check(PM)
        assert hook.type_check(PME)


class TestRegisterModelsHookCollectFromBundle:
    def test_it_works_vendor_one(self, db, hook: RegisterModelsHook):
        hook.run_hook(None, [VendorOneBundle])
        expected_one = get_vendor_one_models()
        assert hook.store.models == expected_one
        assert db.metadata.tables == _to_metadata_tables(expected_one)

    def test_it_works_vendor_two(self, db, hook: RegisterModelsHook):
        hook.run_hook(None, [VendorTwoBundle])
        expected_two = get_vendor_two_models()
        assert hook.store.models == expected_two
        assert db.metadata.tables == _to_metadata_tables(expected_two)

    def test_it_works_vendor_one_and_two(self, db, hook: RegisterModelsHook):
        hook.run_hook(None, [VendorOneBundle, VendorTwoBundle])
        expected_both = {**get_vendor_one_models(),
                         **get_vendor_two_models()}
        assert hook.store.models == expected_both
        assert db.metadata.tables == _to_metadata_tables(expected_both)

    def test_vendor_bundle_subclassing(self, db, hook: RegisterModelsHook):
        hook.run_hook(None, [ExtVendorOneBundle])
        expected_ext_one = get_ext_vendor_one_models()
        assert hook.store.models == expected_ext_one
        assert hasattr(hook.store.models['OneBasic'], 'ext')
        assert db.metadata.tables == _to_metadata_tables(expected_ext_one)

    def test_vendor_bundle_subsubclassing(self, db, hook: RegisterModelsHook):
        hook.run_hook(None, [ExtExtVendorOneBundle])
        expected_ext_ext_one = get_ext_ext_vendor_one_models()
        assert hook.store.models == expected_ext_ext_one
        assert db.metadata.tables == _to_metadata_tables(expected_ext_ext_one)

    def test_lazy_backrefs_throw_exception(self, hook: RegisterModelsHook):
        with pytest.raises(Exception) as e:
            hook.run_hook(None, [BackrefBundle])
        error = 'Discovered a lazy-mapped backref `backrefs` on ' \
                '`tests._bundles.backref.models.OneRelationship`. Currently ' \
                'this is unsupported; please use `db.relationship` with '\
                'the `back_populates` kwarg on both sides instead.'
        assert error in str(e)
