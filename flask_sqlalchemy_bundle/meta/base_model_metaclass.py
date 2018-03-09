from flask_sqlalchemy.model import DefaultMeta

from .model_meta_factory import ModelMetaFactory
from .model_registry import _model_registry
from .types import McsArgs, McsInitArgs
from .utils import deep_getattr


class BaseModelMetaclass(DefaultMeta):
    def __new__(mcs, name, bases, clsdict):
        mcs_args = McsArgs(mcs, name, bases, clsdict)
        _model_registry._ensure_correct_base_model(mcs_args)

        model_meta_factory_class = deep_getattr(
            clsdict, mcs_args.bases, '_meta_factory_class', ModelMetaFactory)
        model_meta_factory: ModelMetaFactory = model_meta_factory_class()
        model_meta_factory._contribute_to_class(mcs_args)

        if model_meta_factory.abstract:
            return super().__new__(*mcs_args)

        _model_registry.register_new(mcs_args)
        return super().__new__(*mcs_args)

    def __init__(cls, name, bases, clsdict):
        if cls._meta.abstract or not cls._meta.lazy_mapped:
            super().__init__(name, bases, clsdict)
        if not cls._meta.abstract:
            _model_registry.register(McsInitArgs(cls, name, bases, clsdict))
