# Flask SQLAlchemy Bundle

Integrates SQLAlchemy into Flask Unchained applications by standing on the shoulders of giants:
* [SQLAlchemy](http://www.sqlalchemy.org/) and [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/)
* [Alembic](http://alembic.zzzcomputing.com/en/latest/) and [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)

## Quick Start

### 1. Install:

```bash
$ pip install flask_sqlalchemy_bundle
```

### 2. Add it to your `BUNDLES`:

```python
# app/config.py
from flask_unchained import AppConfig

class BaseConfig(AppConfig):
    BUNDLES = [
        'flask_sqlalchemy_bundle',
        # ...
    ]
```

### 3. Configure:

Flask SQLAlchemy Bundle is configured to work out-of-the-box using an SQLite database. This is fine for getting started quickly, but it's probably not what you want for more serious work. This bundle supports all of the standard [Flask-SQLAlchemy settings](http://flask-sqlalchemy.pocoo.org/latest/config/):

```python
# app/config.py
import os
from flask_unchained import AppConfig

class BaseConfig(AppConfig):
    # ...
    SQLALCHEMY_DATABASE_URI = '{engine}://{user}:{pw}@{host}:{port}/{db}'.format(
        engine=os.getenv('FLASK_DATABASE_ENGINE', 'postgresql+psycopg2'),
        user=os.getenv('FLASK_DATABASE_USER', 'flask_app'),
        pw=os.getenv('FLASK_DATABASE_PASSWORD', 'flask_app'),
        host=os.getenv('FLASK_DATABASE_HOST', '127.0.0.1'),
        port=os.getenv('FLASK_DATABASE_PORT', 5432),
        db=os.getenv('FLASK_DATABASE_NAME', 'flask_app'))

class DevConfig(BaseConfig):
    SQLALCHEMY_ECHO = True

class TestConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # :memory:
```

### 4. Create some models

```python
# app/models/__init__.py
from flask_sqlalchemy_bundle import db

# by default, models have a primary key column named `id`, and they are also
# timestamped, on columns `created_at` and `updated_at`. This is configurable:
class Basic(db.Model):
    class Meta:
        pk = 'identity'  # rename the primary key column to `identity`
        created_at = 'created'  # rename created_at column to `created`
        updated_at = None  # do not include the updated_at column
        
    # generated columns:
    # identity = db.Column(db.Integer, primary_key=True)
    # created = db.Column(db.DateTime, server_default=sa_func.now())

class Parent(db.Model):
    name = db.Column(db.String)
    children = db.relationship('Child', back_populates='parent')

# we include a foreign_key helper to make relationships a bit easier:
class Child(db.Model):
    name = db.Column(db.String)
    parent_id = db.foreign_key('Parent')
    parent = db.relationship('Parent', back_populates='children')
```

Flask SQLAlchemy Bundle also includes a few more meta options to make your life easier, including nearly automatic support for [polymorphic models](http://docs.sqlalchemy.org/en/latest/orm/inheritance.html):

```python
from flask_sqlalchemy_bundle import db

class Person(db.Model):
    class Meta:
        # this is the only option required to enable polymorphic inheritance:
        polymorphic = True  # 'joined' by default, or you can use 'single'
        # its options are configurable:
        polymorphic_on = 'discriminator'  # default discriminator column name
        polymorphic_identity = 'Person'  # default identity is the class name
    name = db.Column(db.String)

class Employee(Person):
    # when using 'joined', the primary key column automatically gets set to a
    # foreign key to the base class
    # id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    badge_number = db.Column(db.Integer)

class Manager(Employee):
    # multiple levels of inheritance are supported for the automatic primary key:
    # id = db.Column(db.Integer, db.ForeignKey('employee.id'), primary_key=True)
    rank = db.Column(db.String)
```

### 5. Run migrations

```bash
$ flask db migrate -m 'create example models'
$ flask db upgrade
```

## Advanced: Customizing the base model class and/or meta options

Let's look at how to do both, because they are closely related. In this example we're going to add a new meta option, as well as create an alias for the `query` attribute on model classes.

### Start by extending `flask_sqlalchemy_bundle.BaseModel`:

```python
# app/extensions/sqlalchemy/base_model.py
from flask_sqlalchemy_bundle import BaseModel
from flask_sqlalchemy_bundle.meta import McsArgs, MetaOption, ModelMetaFactory


class ExtendExistingMetaOption(MetaOption):
    def __init__(self):
        super().__init__(name='extend_existing', default=False, inherit=False)

    def check_value(self, value, mcs_args: McsArgs):
        msg = f'{self.name} Meta option on {mcs_args.model_repr} ' \
              f'must be True or False'
        assert isinstance(value, bool), msg

    def contribute_to_class(self, mcs_args: McsArgs, value):
        if not value:
            return

        table_args = mcs_args.clsdict.get('__table_args__', {})
        table_args['extend_existing'] = True
        mcs_args.clsdict['__table_args__'] = table_args


class CustomModelMetaFactory(ModelMetaFactory):
    def _get_model_meta_options(self):
        # it's very important to call super() here!
        return super()._get_model_meta_options() + [
            ExtendExistingMetaOption(),
        ]


class QueryAliasDescriptor:
    def __get__(self, instance, cls):
        return cls.query


class CustomBaseModel(BaseModel):
    # set the _meta_factory_class attribute to specify your custom factory.
    _meta_factory_class = CustomModelMetaFactory
    # You can also set this on subclasses of db.Model, but of course, normal
    # Python inheritance rules apply. So it only has to be declared on the base
    # model class passed to the SQLAlchemy extension constructor if you want
    # *all* model classes to have your customized meta factory.

    class Meta:
        abstract = True  # tell SQLAlchemy not to map this class
        extend_existing = True  # might as well use our custom meta option!

        # disable automatic timestamps for all models (these particular options
        # will get inherited by all subclasses, though they themselves can
        # override the defaults we're defining here)
        created_at = None
        updated_at = None

    # make SomeModel.q equivalent to using SomeModel.query
    q = QueryAliasDescriptor()
```

### Next, override the `db` extension using your custom base model:

```python
# app/extensions/__init__.py
from flask_sqlalchemy_bundle import SQLAlchemy
from sqlalchemy import MetaData

from .sqlalchemy.base_model import CustomBaseModel

db = SQLAlchemy(model_class=CustomBaseModel, metadata=MetaData(naming_convention={
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}))

EXTENSIONS = {
    'db': db,
}
```

Normally, that's all that would be required to override an extension instance from a vendor bundle. However, the `db` extension is special because code uses it at import-time to declare models, and thus we need to manually register our new instance with Flask Unchained (this must be done in the same file as your app bundle class, because that's the very first file the Unchained AppFactory will import/execute when it starts your app):

```python
# app/__init__.py
from flask_unchained import AppBundle, unchained

from .extensions import db
unchained.extensions.db = db

class YourAppBundle(AppBundle):
    pass
```

Now, there's a fair bit of magic happening behind the scenes to make this work. You can continue using `from flask_sqlalchemy_bundle import db` to declare all your models, and they will automatically use your custom base model (as will models from any vendor bundles you've included). However, if you need to use the `db` extension to do anything other than declare models, then you must use the correct instance (namely, the one you instantiated in your app bundle's extensions package). This means that you should always use Unchained's dependency injection to get access to extensions, because it will automatically make sure you're given the correct instance. (Within your app bundle, it's safe to directly import and use the instance you created, but any code meant to be distributed for use in other Unchained apps must use dependency injection.)
