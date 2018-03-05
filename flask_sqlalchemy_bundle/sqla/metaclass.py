from collections import defaultdict
from flask_sqlalchemy.model import DefaultMeta
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.interfaces import MapperProperty


def _normalize_model_meta(meta):
    d = {'lazy_mapping': getattr(meta, 'lazy_mapping', False),
         'relationships': getattr(meta, 'relationships', {}),
         }

    return type('Meta', (object,), d)


class ModelMeta(DefaultMeta):
    """
    This code defers the registration of (some) model classes with SQLAlchemy.
    This allows for an external process (namely, RegisterModelsHook) to decide
    which model classes it wants the Mapper to know about. In effect this makes
    it possible for a vendor bundle subclass (or the user's app bundle) to
    override models found in other bundles(*) by defining a new model with the
    same class name.
    (*) a model must declare itself extendable and/or overridable::

        class SomeModel(db.PrimaryKeyModel):
            class Meta:
                lazy_mapping = True

            # ... (everything else is the same as normal)
    """
    def __new__(mcs, name, bases, clsdict):
        if '__abstract__' in clsdict:
            return super().__new__(mcs, name, bases, clsdict)

        if name in _ModelRegistry._registry:
            bases = _ModelRegistry.convert_bases_to_mixins(bases)

        meta = clsdict.pop('Meta', None)
        clsdict['_meta'] = _normalize_model_meta(meta)

        _ModelRegistry.register_new(mcs, name, bases, clsdict)

        return super().__new__(mcs, name, bases, clsdict)

    def __init__(cls, name, bases, clsdict):
        is_concrete = '__abstract__' not in clsdict
        is_lazy = is_concrete and cls._meta.lazy_mapping
        if not is_concrete or not is_lazy:
            if is_concrete:
                print('initializing', name)
            super().__init__(name, bases, clsdict)

        if is_concrete:

            for k, v in clsdict.items():
                if isinstance(v, RelationshipProperty):
                    print('!!!!!!!! rel!!', name, k, v.argument)

            _ModelRegistry.register(cls, name, bases, clsdict)
            if not is_lazy:
                _ModelRegistry._initialized[name] = cls


class _ModelRegistry:
    # all discovered models "classes", before type.__new__ has been called:
    # - keyed by model class name
    # - values are lists of tuples of (model_mcs, name, bases, clsdict)
    # - order of keys signifies discovery order at import time
    # - order of list items signifies inheritance order (earlier tuples are base
    #   classes; last tuple is the subclass that will end up getting created)
    _registry = defaultdict(list)

    # actual model classes awaiting initialization (after type.__new__ but
    # before type.__init__):
    # - keyed by model class name
    # - values are tuples of (model_cls, name, bases, clsdict)
    _models = {}

    _relationships = defaultdict(dict)

    # which keys in _models have already been initialized
    _initialized = {}

    @classmethod
    def register_new(cls, model_mcs, name, bases, clsdict):
        cls._registry[name].append((model_mcs, name, bases, clsdict))

    @classmethod
    def register(cls, model_cls, name, bases, clsdict):
        cls._models[name] = (model_cls, name, bases, clsdict)
        relationships = model_cls._meta.relationships
        if relationships:
            cls._relationships[name] = relationships

    @classmethod
    def finish_initializing(cls):
        # this outer loop is used to perform initializations in the order the
        # classes were originally discovered (ie at import time)
        for name in cls._registry:
            if cls.should_initialize(name):
                model_cls, name, bases, clsdict = cls._models[name]
                print('delayed initializing', name)
                super(ModelMeta, model_cls).__init__(name, bases, clsdict)
                cls._initialized[name] = model_cls
        return cls._initialized

    @classmethod
    def should_initialize(cls, model_name):
        if model_name in cls._initialized:
            return False

        if model_name not in cls._relationships:
            return True

        for related_model_name in cls._relationships[model_name]:
            related_model = cls._models[related_model_name][0]

            other_side = cls._relationships[related_model_name].values()
            for related_attr in other_side:
                if hasattr(related_model, related_attr):
                    return True

    @classmethod
    def convert_bases_to_mixins(cls, bases):
        """
        For each base class in bases that the _ModelRegistry knows about, create a
        replacement class containing the methods and attributes from the base class:
         - the mixin should only extend object (not db.PrimaryKeyModel)
         - if any of the attributes are MapperProperty instances (eg relationship,
           association_proxy, etc), then turn them into @declared_attr properties
        """
        new_bases = []

        for b in reversed(bases):
            if b.__name__ not in cls._registry:
                new_bases.append(b)
                continue

            _, base_name, base_bases, base_clsdict = \
                cls._registry[b.__name__][-1]

            new_bases += reversed(base_bases)

            clsdict = {}
            for attr, value in base_clsdict.items():
                if not isinstance(value, MapperProperty):
                    clsdict[attr] = value
                else:
                    # programmatically add a method wrapped with declared_attr
                    # to the new mixin class
                    exec(f"""\
@declared_attr
def {attr}(cls):
    return value""", {'value': value, 'declared_attr': declared_attr}, clsdict)

            new_bases.append(type(f'{base_name}Mixin', (object,), clsdict))

        return tuple(reversed(new_bases))
