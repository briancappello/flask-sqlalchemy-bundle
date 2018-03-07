from flask_sqlalchemy.model import DefaultMeta

from .model_meta_factory import ModelMetaFactory
from .model_registry import _model_registry
from .types import MetaInitArgs, MutableMetaArgs
from .utils import deep_getattr


class BaseModelMetaclass(DefaultMeta):
    def __new__(mcs, name, bases, clsdict):
        meta_args = MutableMetaArgs(mcs, name, bases, clsdict)
        _model_registry._ensure_correct_base_model(meta_args)

        model_meta_factory_class = deep_getattr(
            clsdict, meta_args.bases, '_meta_factory_class', ModelMetaFactory)
        model_meta_factory: ModelMetaFactory = model_meta_factory_class()
        model_meta_factory._contribute_to_class(meta_args)

        if model_meta_factory.abstract:
            return super().__new__(*meta_args)

        _model_registry.register_new(meta_args)
        return super().__new__(*meta_args)

    def __init__(cls, name, bases, clsdict):
        if cls._meta.abstract or not cls._meta.lazy_mapped:
            super().__init__(name, bases, clsdict)
        if not cls._meta.abstract:
            _model_registry.register(MetaInitArgs(cls, name, bases, clsdict))
