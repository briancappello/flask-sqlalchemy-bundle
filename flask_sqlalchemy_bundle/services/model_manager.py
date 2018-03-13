from flask_unchained import BaseService, injectable, unchained
from sqlalchemy.orm.exc import NoResultFound
from typing import *

from ..base_model import BaseModel as Model
from ..base_query import BaseQuery
from .session_manager import SessionManager


class ModelManager(BaseService):
    __abstract__ = True

    # FIXME there must *some* way to get these fscking type hints to understand
    # that they're returning a specific subclass of db.Model as set by this attr
    model: Type[Model] = Model

    def __init__(self, session_manager: SessionManager = injectable):
        self.session_manager = session_manager
        if isinstance(self.model, str):
            self.model = unchained.flask_sqlalchemy_bundle.models[self.model]

    @property
    def q(self) -> BaseQuery:
        return self.model.query

    def create(self, **kwargs) -> model:
        instance = self.model(**kwargs)
        self.session_manager.add(instance)
        return instance

    def update(self, instance, **kwargs) -> model:
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        self.session_manager.add(instance)
        return instance

    def get(self, id) -> Union[None, model]:
        return self.q.get(int(id))

    def get_or_create(self, **kwargs) -> Tuple[model, bool]:
        """
        :return: returns a tuple of the instance and a boolean flag specifying
        whether or not the instance was created
        """
        instance = self.get_by(**kwargs)
        if not instance:
            return self.create(**kwargs), True
        return instance, False

    def get_by(self, **kwargs) -> Union[None, model]:
        try:
            return self.q.filter_by(**kwargs).one()
        except NoResultFound:
            return None

    def find_all(self) -> List[model]:
        return self.q.all()

    def find_by(self, **kwargs) -> List[model]:
        return self.q.filter_by(**kwargs).all()
