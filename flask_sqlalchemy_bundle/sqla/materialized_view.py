from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement


# SQLAlchemy PostgreSQL Materialized Views
# http://www.jeffwidman.com/blog/847/using-sqlalchemy-to-create-and-manage-postgresql-materialized-views/

def _create_materialized_view(name, selectable, db):
    # must use a temporary metadata here so that SQLAlchemy doesn't detect the
    # table as "standalone". (it will still use the correct metadata once
    # attached to the __table__ attribute of the declarative base model)
    table = db.Table(name, db.MetaData())
    for col in selectable.c:
        table.append_column(
            db.Column(col.name, col.type, primary_key=col.primary_key))

    if not any([col.primary_key for col in selectable.c]):
        table.append_constraint(
            db.PrimaryKeyConstraint(*[col.name for col in selectable.c]))

    # # to support using db.create_all()
    db.event.listen(db.metadata, 'after_create',
                    _CreateMaterializedView(name, selectable))

    # to support using db.create_all()
    @db.event.listens_for(db.metadata, 'after_create')
    def create_indexes(target, connection, **kwargs):
        for idx in table.indexes:
            idx.create(connection)

    # to support using db.drop_all()
    db.event.listen(db.metadata, 'before_drop',
                    db.DDL(f'DROP MATERIALIZED VIEW IF EXISTS {name}'))

    return table


def _refresh_materialized_view(name, concurrently=True, db=None):
    concurrently = concurrently and 'CONCURRENTLY ' or ''
    db.session.execute(f'REFRESH MATERIALIZED VIEW {concurrently}{name}')


def _refresh_all_materialized_views(concurrently=True, db=None):
    materialized_views = db.inspect(db.engine).get_view_names(include='materialized')
    for materialized_view in materialized_views:
        _refresh_materialized_view(materialized_view, concurrently, db)


# to support using db.create_all()
class _CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


# to support using db.create_all()
@compiles(_CreateMaterializedView)
def _compile_create_materialized_view(element, compiler, **kwargs):
    return 'CREATE MATERIALIZED VIEW {name} AS {query}'.format(
        name=element.name,
        query=compiler.sql_compiler.process(element.selectable,
                                            literal_binds=True)
    )
