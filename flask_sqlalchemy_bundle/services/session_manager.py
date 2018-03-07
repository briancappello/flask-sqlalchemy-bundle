from flask_unchained import BaseService
from typing import *

from ..extensions import db


class SessionManager(BaseService):
    def add(self, instance: db.Model, commit: bool = False):
        db.session.add(instance)
        if commit:
            self.commit()

    def add_all(self, instances: List[db.Model], commit: bool = False):
        db.session.add_all(instances)
        if commit:
            self.commit()

    def delete(self, instance: db.Model, commit: bool = False):
        db.session.delete(instance)
        if commit:
            self.commit()

    def commit(self):
        db.session.commit()

    def __getattr__(self, method_name):
        return getattr(db.session, method_name)
