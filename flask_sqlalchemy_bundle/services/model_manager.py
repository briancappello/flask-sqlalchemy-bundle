from flask_sqlalchemy import BaseQuery
from flask_unchained import BaseService, unchained
from typing import *

from ..extensions import db
from .session_manager import SessionManager


class ModelManager(BaseService):
    __abstract__ = True

    model: Type[db.BaseModel]

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        if isinstance(self.model, str):
            self.model = unchained.flask_sqlalchemy_bundle.models[self.model]

    @property
    def q(self) -> BaseQuery:
        return self.model.query

    def create(self, **kwargs) -> db.BaseModel:
        instance = self.model(**kwargs)
        self.session_manager.add(instance)
        return instance

    def update(self, instance, **kwargs) -> db.BaseModel:
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        self.session_manager.add(instance)
        return instance

    def get(self, id) -> db.BaseModel:
        return self.q.get(int(id))

    def get_or_create(self, **kwargs) -> Tuple[db.BaseModel, bool]:
        """
        :return: returns a tuple of the instance and a boolean flag specifying
        whether or not the instance was created
        """
        instance = self.get_by(**kwargs)
        if not instance:
            return self.create(**kwargs), True
        return instance, False

    def get_by(self, **kwargs) -> db.BaseModel:
        return self.q.filter_by(**kwargs).first()

    def find_all(self) -> List[db.BaseModel]:
        return self.q.all()

    def find_by(self, **kwargs) -> List[db.BaseModel]:
        return self.q.filter_by(**kwargs).all()
