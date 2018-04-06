# CHANGELOG

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
