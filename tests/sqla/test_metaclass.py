import pytest

from flask_sqlalchemy_bundle.sqla.metaclass import _model_registry


def _names(bases):
    return [b.__name__ for b in bases]


@pytest.mark.bundles(['tests._bundles.deeply_nested_mixins'])
class TestConvertBasesOrder:
    def test_it_works(self):
        from .._bundles.deeply_nested_mixins.models import B3
        result = _model_registry._registry[B3.__name__][B3.__module__].bases
        assert _names(result) == [
            'B1ConvertedMixin', 'B2ConvertedMixin', 'Model']

    def test_it_preserves_order_multiple_inheritance(self):
        from .._bundles.deeply_nested_mixins.models import B5
        result = _model_registry._registry[B5.__name__][B5.__module__].bases
        assert _names(result) == [
            'B4ConvertedMixin', 'B3ConvertedMixin', 'B1ConvertedMixin',
            'B2ConvertedMixin', 'Model']

    def test_it_works_deeply_nested_multiple_inheritance(self):
        from .._bundles.deeply_nested_mixins.models import B7
        result = _model_registry._registry[B7.__name__][B7.__module__].bases
        assert _names(result) == [
            'B5ConvertedMixin', 'B4ConvertedMixin', 'B3ConvertedMixin',
            'B1ConvertedMixin', 'B2ConvertedMixin', 'B6ConvertedMixin',
            'Model', 'GenericMixin']
