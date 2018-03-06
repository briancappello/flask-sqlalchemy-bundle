"""
This code defers the registration of (some) model classes with SQLAlchemy.
This allows for an external process to decide which model classes it wants
the Mapper to know about. In effect this makes it possible for a vendor
bundle subclass (or the user's app bundle) to extend or override models from
other bundles by defining a new model with the same name. In order for this to
work, a model must declare itself extendable and/or overridable::

    class SomeModel(db.PrimaryKeyModel):
        class Meta:
            lazy_mapping = True

        # ... (everything else is the same as normal)
"""
import warnings
from collections import defaultdict, namedtuple
from flask_sqlalchemy.model import DefaultMeta
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.interfaces import MapperProperty
from typing import *

_missing = object()


MetaNewArgs = namedtuple('MetaNewArgs', ('mcs', 'name', 'bases', 'clsdict'))
MetaInitArgs = namedtuple('MetaInitArgs', ('cls', 'name', 'bases', 'clsdict'))


class MutableMetaArgs:
    def __init__(self, mcs, name, bases, clsdict):
        self.mcs = mcs
        self.name = name
        self.bases = bases
        self.clsdict = clsdict

    @property
    def module(self):
        return self.clsdict['__module__']

    @property
    def model_repr(self):
        return f'{self.module}.{self.name}'

    @property
    def model_meta_options(self):
        return self.clsdict['_meta']


    def __iter__(self):
        return iter([self.mcs, self.name, self.bases, self.clsdict])

    def __repr__(self):
        return f'<MutableMetaArgs model={self.model_repr}>'


def deep_getattr(clsdict, bases, name, default=_missing):
    value = clsdict.get(name, _missing)
    if value != _missing:
        return value
    for base in bases:
        value = getattr(base, name, _missing)
        if value != _missing:
            return value
    if default != _missing:
        return default
    raise AttributeError(name)


class ModelMetaOption:
    def __init__(self, name, default=None, inherit=False):
        self.name = name
        self.default = default
        self.inherit = inherit

    def get_value(self, model_meta, base_model_meta):
        """
        :param model_meta: the class Meta (if any) from the user's model (NOTE:
            this is NOT an instance of ModelMetaOptions)
        :param base_model_meta: the ModelMetaOptions from the user's model's base class
        """
        value = self.default
        if self.inherit and base_model_meta is not None:
            value = getattr(base_model_meta, self.name, value)
        if model_meta is not None:
            value = getattr(model_meta, self.name, value)
        return value

    def check_value(self, model_meta_options, value):
        pass

    def contribute_to_class(self, meta_args: MutableMetaArgs, model_meta_options):
        pass

    def __repr__(self):
        return f'<{self.__class__.__name__} name={self.name!r}, ' \
               f'value={self.default!r}, inherit={self.inherit}>'


class RelationshipsOption(ModelMetaOption):
    def __init__(self):
        super().__init__('relationships', default={}, inherit=True)

    def get_value(self, model_meta, base_model_meta):
        """overridden to merge with inherited value"""
        value = getattr(base_model_meta, self.name, self.default)
        value.update(getattr(model_meta, self.name, self.default))
        return value

    def contribute_to_class(self, meta_args: MutableMetaArgs, model_meta_options):
        _, name, bases, clsdict = meta_args
        discovered_relationships = {}

        def discover_relationships(d):
            for k, v in d.items():
                if isinstance(v, RelationshipProperty):
                    discovered_relationships[v.argument] = k
                    if v.backref and model_meta_options.lazy_mapping:
                        raise Exception(
                            f'Discovered a lazy-mapped backref `{k}` on '
                            f'`{meta_args.module}.{name}`. Currently this '
                            'is unsupported; please use `db.relationship` with '
                            'the `back_populates` kwarg on both sides instead.')

        for base in bases:
            discover_relationships(vars(base))
        discover_relationships(clsdict)

        model_meta_options.relationships.update(discovered_relationships)


class ModelMetaOptions:
    def __init__(self):
        self._meta_args: MutableMetaArgs = None

    def get_model_meta_options(self) -> List[ModelMetaOption]:
        """"
        Define fields allowed in the Meta class on end-user models, and the
        behavior of each.

        Custom ModelMetaOptions classes should override this method to customize
        the options supported on class Meta of end-user models.
        """
        return [
            ModelMetaOption('lazy_mapping', default=False, inherit=True),
            RelationshipsOption(),  # must be after lazy_mapping
        ]

    def contribute_to_class(self, meta_args: MutableMetaArgs):
        self._meta_args = meta_args

        meta = meta_args.clsdict.pop('Meta', None)
        base_model_meta = deep_getattr({}, meta_args.bases, '_meta', None)

        meta_args.clsdict['_meta'] = self
        self._fill_from_meta(meta, base_model_meta)

        for option in self.get_model_meta_options():
            option.contribute_to_class(meta_args, self)

    def _fill_from_meta(self, meta, base_model_meta):
        # Exclude private/protected fields from the meta
        meta_attrs = {} if not meta else {k: v for k, v in vars(meta).items()
                                          if not k.startswith('_')}

        for option in self.get_model_meta_options():
            assert not hasattr(self, option.name), \
                f"Can't override field {option.name}."
            value = option.get_value(meta, base_model_meta)
            option.check_value(self, value)
            meta_attrs.pop(option.name, None)
            setattr(self, option.name, value)

        if meta_attrs:
            # Some attributes in the Meta aren't allowed here
            raise TypeError(
                f"'class Meta' for {self._meta_args.model_repr!r} got unknown "
                f"attribute(s) {','.join(sorted(meta_attrs.keys()))}")

    def __repr__(self):
        return '<{cls} model={model!r} model_meta_options={attrs!r}>'.format(
            cls=self.__class__.__name__,
            model=self._meta_args.model_repr,
            attrs={option.name: getattr(self, option.name)
                   for option in self.get_model_meta_options()})


class SQLAlchemyBaseModelMeta(DefaultMeta):
    def __new__(mcs, name, bases, clsdict):
        if '__abstract__' in clsdict:
            return super().__new__(mcs, name, bases, clsdict)

        meta_args = MutableMetaArgs(mcs, name, bases, clsdict)

        model_meta_options_class = deep_getattr(
            clsdict, bases, '_model_meta_options_class', ModelMetaOptions)
        model_meta_options: ModelMetaOptions = model_meta_options_class()
        model_meta_options.contribute_to_class(meta_args)

        _model_registry.register_new(meta_args)
        return super().__new__(*meta_args)

    def __init__(cls, name, bases, clsdict):
        is_concrete = '__abstract__' not in clsdict
        is_lazy = is_concrete and cls._meta.lazy_mapping
        if not is_lazy:
            super().__init__(name, bases, clsdict)
        if is_concrete:
            _model_registry.register(MetaInitArgs(cls, name, bases, clsdict),
                                     is_lazy)


class _ModelRegistry:
    def __init__(self):
        # all discovered models "classes", before type.__new__ has been called:
        # - keyed by model class name
        # - order of keys signifies model class discovery order at import time
        # - values are a lookup of:
        #   - keys: module name of this particular model class
        #   - values: MetaNewArgs(model_mcs, name, bases, clsdict)
        # this dict is used for inspecting base classes when __new__ is
        # called on a model class that extends another of the same name
        self._registry: Dict[str, Dict[str, MetaNewArgs]] = defaultdict(dict)

        # actual model classes awaiting initialization (after type.__new__ but
        # before type.__init__):
        # - keyed by model class name
        # - values are MetaInitArgs(model_cls, name, bases, clsdict)
        # this lookup contains the knowledge of which version of a model class
        # should maybe get mapped (SQLAlchemyBaseModelMeta populates this dict
        # via the register method - insertion order of the correct version of a
        # model class by name is therefore determined by the import order of
        # bundles' models modules (essentially, by the RegisterModelsHook))
        self._models: Dict[str, MetaInitArgs] = {}

        # like self._models, except its values are the relationships each model
        # class name expects on the other side
        # - keyed by model class name
        # - values are a dict:
        #   - keyed by the model name on the other side
        #   - value is the attribute expected to exist
        self._relationships: Dict[str, Dict[str, str]] = {}

        # which keys in self._models have already been initialized
        self._initialized: Set[str] = set()

    def _reset(self):
        self._registry = defaultdict(dict)
        self._models = {}
        self._relationships = {}
        self._initialized = set()

    def register_new(self, meta_args: MutableMetaArgs):
        mcs, name, bases, clsdict = meta_args
        if (name in self._registry
                and not meta_args.model_meta_options.polymorphic):
            meta_args.bases = self._convert_bases_to_mixins(bases)
        self._registry[name][meta_args.module] = \
            MetaNewArgs(mcs, name, bases, clsdict)

    def register(self, meta_args: MetaInitArgs, is_lazy: bool):
        self._models[meta_args.name] = meta_args
        if not is_lazy:
            self._initialized.add(meta_args.name)

        relationships = meta_args.cls._meta.relationships
        if relationships:
            self._relationships[meta_args.name] = relationships

    def finalize_mappings(self):
        # this outer loop is needed to perform initializations in the order the
        # classes were originally discovered at import time
        for name in self._registry:
            if self.should_initialize(name):
                model_cls, name, bases, clsdict = self._models[name]
                super(SQLAlchemyBaseModelMeta, model_cls).__init__(name, bases,
                                                                   clsdict)
                self._initialized.add(name)
        return {name: self._models[name].cls for name in self._initialized}

    def should_initialize(self, model_name):
        if model_name in self._initialized:
            return False

        if model_name not in self._relationships:
            return True

        with warnings.catch_warnings():
            # not all related classes will have been initialized yet, ie they
            # might still be non-mapped from SQLAlchemy's perspective, which is
            # safe to ignore here
            filter_re = r'Unmanaged access of declarative attribute \w+ from ' \
                        r'non-mapped class \w+'
            warnings.filterwarnings('ignore', filter_re, SAWarning)

            for related_model_name in self._relationships[model_name]:
                related_model = self._models[related_model_name].cls

                try:
                    other_side_relationships = \
                        self._relationships[related_model_name]
                except KeyError:
                    related_model_module = \
                        self._models[related_model_name].cls.__module__
                    raise KeyError(
                        'Incomplete `relationships` Meta declaration for '
                        f'{related_model_module}.{related_model_name} '
                        f'(missing {model_name})')

                if model_name not in other_side_relationships:
                    continue
                related_attr = other_side_relationships[model_name]
                if hasattr(related_model, related_attr):
                    return True

    def _convert_bases_to_mixins(self, bases):
        """
        For each base class in bases that the _ModelRegistry knows about, create
        a replacement class containing the methods and attributes from the base
        class:
         - the mixin should only extend object (not db.PrimaryKeyModel)
         - if any of the attributes are MapperProperty instances (relationship,
           association_proxy, etc), then turn them into @declared_attr props
        """
        new_bases = []
        for b in reversed(bases):
            if b.__name__ not in self._registry:
                new_bases.append(b)
                continue

            _, base_name, base_bases, base_clsdict = \
                self._registry[b.__name__][b.__module__]

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
def {attr}(self):
    return value""", {'value': value, 'declared_attr': declared_attr}, clsdict)

            new_bases.append(type(f'{base_name}Mixin', (object,), clsdict))

        return tuple(reversed(new_bases))


_model_registry = _ModelRegistry()
