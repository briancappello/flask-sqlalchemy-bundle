# CHANGELOG

## 0.3.1 (unreleased)

* fix required validator
* support using translations in validation error messages

## 0.3.0 (2018/07/14)

* fix `render_migration_item` when second argument is `None`
* add `commit` kwarg to `ModelManager.get_or_create`
* add support for validation on sqlalchemy models

## 0.2.1 (2018/04/08)

* bugfix: Query.get should accept a tuple (for composite primary keys)

## 0.2.0 (2018/04/06)

* add ModelManager and SessionManager service classes
* support extending the SQLAlchemy extension and specifying a custom model
* add a bunch of class Meta optional magic
    * automatic primary key columns
    * automatic time stamping
    * improved polymorphic mapping
    * improved materialized views
* add some pytest fixtures
* add a bunch of tests
* support lazy-mapped model classes
* add support for PostgreSQL materialized views
* switch from Flask-Alembic to Flask-Migrate

## 0.1.0

* initial release
