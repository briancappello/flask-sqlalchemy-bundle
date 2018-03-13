import pytest

from flask_sqlalchemy_bundle import ModelManager
from flask_sqlalchemy_bundle.meta.model_registry import _model_registry
from flask_unchained import unchained
from sqlalchemy.sql.expression import case, label, literal
from tests.conftest import POSTGRES


def setup(db):
    class Node(db.Model):
        class Meta:
            lazy_mapped = False

        slug = db.Column(db.String, index=True, unique=True)

        parent_id = db.foreign_key('Node', nullable=True)
        parent = db.relationship('Node', back_populates='children',
                                 remote_side='Node.id')
        children = db.relationship('Node', back_populates='parent')

        mv = db.relationship('NodeMV', uselist=False, foreign_keys='NodeMV.id',
                             primaryjoin='Node.id == NodeMV.id')
        depth = db.association_proxy('mv', 'depth')
        path = db.association_proxy('mv', 'path')

        __repr_props__ = ('id', 'name', 'path')

    class NodeMV(db.MaterializedView):
        class Meta:
            lazy_mapped = False
            table = 'node_mv'

        @classmethod
        def selectable(cls):
            _cte = (db.select([Node.id.label('id'),
                               literal(0).label('depth'),
                               literal('/').label('path')])
                    .where(Node.parent_id == None)
                    .cte(name='nodes_cte', recursive=True))
            _union = _cte.union_all(
                db.select([
                    Node.id.label('id'),
                    label('depth', _cte.c.depth + 1),
                    label('path', case([
                        # tuple(if condition, then value),
                        (_cte.c.depth == 0, _cte.c.path + Node.slug),
                    ], else_=_cte.c.path + '/' + Node.slug)),
                ]).select_from(db.join(_cte, Node, _cte.c.id == Node.parent_id))
            )
            return db.select([_union])

    _model_registry.finalize_mappings()
    db.drop_all()
    db.create_all()

    class NodeManager(ModelManager):
        model = Node

    session_manager = unchained.services.session_manager
    return Node, NodeMV, NodeManager(session_manager), session_manager


@pytest.mark.options(SQLALCHEMY_DATABASE_URI=POSTGRES)
class TestIt:
    def test_it(self, db):
        Node, NodeMV, node_manager, session_manager = setup(db)

        index = node_manager.create(slug='index')
        contact = node_manager.create(slug='contact', parent=index)
        about = node_manager.create(slug='about', parent=index)
        about_history = node_manager.create(slug='history', parent=about)
        about_team = node_manager.create(slug='team', parent=about)

        session_manager.commit()
        NodeMV.refresh()

        assert index.slug == 'index'
        assert index.path == '/'
        assert index.depth == 0
        assert contact.path == '/contact'
        assert contact.depth == 1
        assert about.path == '/about'
        assert about.depth == 1
        assert about_history.path == '/about/history'
        assert about_history.depth == 2
        assert about_team.path == '/about/team'
        assert about_team.depth == 2
