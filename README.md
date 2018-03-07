# Flask SQLAlchemy Bundle


## overriding the base model

```python
# your_app_bundle/extensions/__init__.py
from flask_sqlalchemy_bundle import SQLAlchemy, QueryBaseModel

db = SQLAlchemy(model_class=QueryBaseModel)

EXTENSIONS = {
    'db': db,
}

# your_app_bundle/__init__.py
from flask_unchained import AppBundle, unchained

from .extensions import db
unchained.extensions.db = db


class YourAppBundle(AppBundle):
    pass
```


# overriding/customizing the model meta options


```python
from flask_sqlalchemy_bundle import BaseModel, db
from flask_sqlalchemy_bundle.sqla import Column, BigInteger
from flask_sqlalchemy_bundle.sqla.meta import (
    AbstractMetaOption, ColumnMetaOption, MetaOption, ModelMetaFactory)


# here's an example of an option to automatically add a primary key column to
# models. this implementation is included, and is only shown here as an example
# normally you would just import it:
# from flask_sqlalchemy_bundle.sqla.meta import PrimaryKeyColumnMetaOption
class PrimaryKeyColumnMetaOption(ColumnMetaOption):
    def __init__(self, name='pk', default='id', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(BigInteger, primary_key=True)


class ExtendExistingMetaOption(MetaOption):
    def __init__(self):
        super().__init__(name='extend_existing', default=True, inherit=True)

    def contribute_to_class(self, meta_args, value, model_meta_options):
        if model_meta_options.extend_existing:
            table_args = meta_args.clsdict.get('__table_args__', {})
            table_args['extend_existing'] = True
            meta_args.clsdict['__table_args__'] = table_args


class CustomModelMetaFactory(ModelMetaFactory):
    def _get_model_meta_options(self):
        return [
            AbstractMetaOption(),  # always required, and must be first
            PrimaryKeyColumnMetaOption(),
            ExtendExistingMetaOption(),
        ]


class CustomBaseModel(BaseModel):
    _meta_factory_class = CustomModelMetaFactory


class Example(db.Model):
    class Meta:
        extend_existing = True

# the equivalent in stock Flask-SQLAlchemy would be:
class Example(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.BigInteger, primary_key=True)
```
