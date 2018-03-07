import pytest

from flask_unchained import unchained

from tests._bundles.custom_extension.extensions import (
    SQLAlchemy as CustomSQLAlchemy,
    Model as CustomModel)


@pytest.mark.bundles(['tests._bundles.custom_extension',
                      'tests._bundles.vendor_two'])
@pytest.mark.usefixtures('app', 'db')
class TestCustomExtension:
    def test_it_works(self, app, db):
        exts = [db, app.extensions['sqlalchemy'].db, unchained.extensions.db]
        for i, ext in enumerate(exts):
            assert isinstance(ext, CustomSQLAlchemy), i
            assert ext == db, i

    def test_it_uses_the_correct_base_model(self, db):
        assert issubclass(db.Model, CustomModel)

        from ._bundles.vendor_two.models import TwoBasic
        assert issubclass(TwoBasic, CustomModel)
