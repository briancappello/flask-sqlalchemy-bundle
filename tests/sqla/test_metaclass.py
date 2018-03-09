import pytest

from flask_sqlalchemy_bundle.sqla.meta.model_registry import _model_registry


def _names(bases):
    return [b.__name__ for b in bases]


@pytest.mark.bundles(['tests._bundles.deeply_nested_mixins'])
class TestConvertBasesOrder:
    def test_it_works(self):
        from .._bundles.deeply_nested_mixins.models import B3
        result = _model_registry._registry[B3.__name__][B3.__module__].bases
        assert _names(result) == [
            'B1_FSQLAConvertedMixin', 'B2_FSQLAConvertedMixin', 'Model']

    def test_it_preserves_order_multiple_inheritance(self):
        from .._bundles.deeply_nested_mixins.models import B5
        result = _model_registry._registry[B5.__name__][B5.__module__].bases
        assert _names(result) == [
            'B4_FSQLAConvertedMixin', 'B3_FSQLAConvertedMixin',
            'B1_FSQLAConvertedMixin', 'B2_FSQLAConvertedMixin', 'Model']

    def test_it_works_deeply_nested_multiple_inheritance(self):
        from .._bundles.deeply_nested_mixins.models import B7
        result = _model_registry._registry[B7.__name__][B7.__module__].bases
        assert _names(result) == [
            'B5_FSQLAConvertedMixin', 'B4_FSQLAConvertedMixin',
            'B3_FSQLAConvertedMixin', 'B1_FSQLAConvertedMixin',
            'B2_FSQLAConvertedMixin', 'B6_FSQLAConvertedMixin',
            'Model', 'GenericMixin']


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
