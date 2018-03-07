"""
This code defers the registration of (some) model classes with SQLAlchemy.
This allows for an external process to decide which model classes it wants
the Mapper to know about. In effect this makes it possible for a vendor
bundle subclass (or the user's app bundle) to extend or override models from
other bundles by defining a new model with the same name. In order for this to
work, a model must declare itself extendable and/or overridable::

    class SomeModel(db.Model):
        class Meta:
            lazy_mapping = True

        # ... (everything else is the same as normal)
"""
import warnings
from collections import defaultdict, namedtuple
from flask_sqlalchemy.model import DefaultMeta, camel_to_snake_case
from sqlalchemy import func as sa_func, types as sa_types
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.interfaces import MapperProperty
from typing import *

from .column import Column
from .relationships import foreign_key
from .types import BigInteger, DateTime

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
    def _module(self):
        return self.clsdict.get('__module__')

    @property
    def _model_repr(self):
        if self._module:
            return f'{self._module}.{self.name}'
        return self.name

    @property
    def _model_meta_options(self):
        return self.clsdict['_meta']

    def __iter__(self):
        return iter([self.mcs, self.name, self.bases, self.clsdict])

    def __repr__(self):
        return f'<MutableMetaArgs model={self._model_repr}>'


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

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        """
        :param meta: the class Meta (if any) from the user's model (NOTE:
            this will be a plain object, NOT an instance of ModelMetaOptions)
        :param base_model_meta: the ModelMetaOptions (if any) from the
            base class of the user's model
        :param meta_args: the MutableMetaArgs for the user's model class
        """
        value = self.default
        if self.inherit and base_model_meta is not None:
            value = getattr(base_model_meta, self.name, value)
        if meta is not None:
            value = getattr(meta, self.name, value)
        return value

    def check_value(self, value, model_meta_options):
        pass

    def contribute_to_class(self, meta_args: MutableMetaArgs, value,
                            model_meta_options):
        pass

    def __repr__(self):
        return f'<{self.__class__.__name__} name={self.name!r}, ' \
               f'value={self.default!r}, inherit={self.inherit}>'


class ModelColumnMetaOption(ModelMetaOption):
    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        value = super().get_value(meta, base_model_meta, meta_args)
        if value is True:
            value = self.default
        return value

    def check_value(self, value, model_meta_options):
        msg = f'{self.name} Meta option on {model_meta_options._model_repr} ' \
              f'must be a str, bool or None'
        assert value is None or isinstance(value, (bool, str)), msg

    def contribute_to_class(self, meta_args: MutableMetaArgs, col_name,
                            model_meta_options):
        if (model_meta_options.abstract
                or (model_meta_options.polymorphic
                    and not model_meta_options._is_base_model)):
            return

        if col_name and col_name not in meta_args.clsdict:
            meta_args.clsdict[col_name] = self.get_column(model_meta_options)

    def get_column(self, model_meta_options):
        raise NotImplementedError


class PrimaryKeyColumnOption(ModelColumnMetaOption):
    def __init__(self, name='pk', default='id', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(BigInteger, primary_key=True)


class CreatedAtColumnOption(ModelColumnMetaOption):
    def __init__(self, name='created_at', default='created_at', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(DateTime, server_default=sa_func.now())


class UpdatedAtColumnOption(ModelColumnMetaOption):
    def __init__(self, name='updated_at', default='updated_at', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(DateTime,
                      server_default=sa_func.now(), onupdate=sa_func.now())


class RelationshipsOption(ModelMetaOption):
    def __init__(self):
        super().__init__('relationships', inherit=True)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        """overridden to merge with inherited value"""
        if '__abstract__' in meta_args.clsdict:
            return None
        value = getattr(base_model_meta, self.name, {}) or {}
        value.update(getattr(meta, self.name, {}))
        return value

    def contribute_to_class(self, meta_args: MutableMetaArgs, relationships,
                            model_meta_options):
        if model_meta_options.abstract:
            return

        discovered_relationships = {}

        def discover_relationships(d):
            for k, v in d.items():
                if isinstance(v, RelationshipProperty):
                    discovered_relationships[v.argument] = k
                    if v.backref and model_meta_options.lazy_mapping:
                        raise Exception(
                            f'Discovered a lazy-mapped backref `{k}` on '
                            f'`{meta_args._model_repr}`. Currently this '
                            'is unsupported; please use `db.relationship` with '
                            'the `back_populates` kwarg on both sides instead.')

        for base in meta_args.bases:
            discover_relationships(vars(base))
        discover_relationships(meta_args.clsdict)

        relationships.update(discovered_relationships)


class BaseTablenameOption(ModelMetaOption):
    def __init__(self):
        super().__init__('_base_tablename', default=None, inherit=False)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        if base_model_meta and not base_model_meta.abstract:
            bm = base_model_meta._meta_args
            return bm.clsdict.get('__tablename__', camel_to_snake_case(bm.name))


class PolymorphicDiscriminatorColumn(ModelColumnMetaOption):
    def __init__(self, name='polymorphic_on', default='discriminator'):
        super().__init__(name=name, default=default)

    def contribute_to_class(self, meta_args: MutableMetaArgs, col_name,
                            model_meta_options):
        if not model_meta_options.polymorphic:
            return
        super().contribute_to_class(meta_args, col_name, model_meta_options)

        mapper_args = meta_args.clsdict.get('__mapper_args__', {})
        if (model_meta_options._is_base_model
                and 'polymorphic_on' not in mapper_args):
            mapper_args['polymorphic_on'] = meta_args.clsdict[col_name]
        meta_args.clsdict['__mapper_args__'] = mapper_args

    def get_column(self, model_meta_options):
        return Column(sa_types.String)


class PolymorphicJoinedPkColumn(ModelColumnMetaOption):
    def __init__(self):
        super().__init__(name='__ignored_joined_pk', default='this_is_ignored')

    def contribute_to_class(self, meta_args: MutableMetaArgs, value,
                            model_meta_options):
        if model_meta_options.abstract:
            return

        pk = model_meta_options.pk or 'id'
        if (model_meta_options.polymorphic == 'joined'
                and not model_meta_options._is_base_model
                and pk not in meta_args.clsdict):
            meta_args.clsdict[pk] = self.get_column(model_meta_options)

    def get_column(self, model_meta_options):
        return foreign_key(model_meta_options._base_tablename,
                           primary_key=True, fk_col=model_meta_options.pk)


class PolymorphicIdentityOption(ModelMetaOption):
    def __init__(self, name='polymorphic_identity', default=None):
        super().__init__(name=name, default=default, inherit=False)

    def contribute_to_class(self, meta_args: MutableMetaArgs, identifier,
                            model_meta_options):
        if not model_meta_options.polymorphic:
            return

        mapper_args = meta_args.clsdict.get('__mapper_args__', {})
        if 'polymorphic_identity' not in mapper_args:
            mapper_args['polymorphic_identity'] = identifier or meta_args.name
        meta_args.clsdict['__mapper_args__'] = mapper_args


class PolymorphicOption(ModelMetaOption):
    def __init__(self):
        super().__init__('polymorphic', default=False, inherit=True)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        value = super().get_value(meta, base_model_meta, meta_args)
        if value and not isinstance(value, str):
            return 'joined'
        return value

    def check_value(self, value, model_meta_options):
        valid = ['joined', 'single', True, False]
        msg = '{name} Meta option on {model} must be one of {choices}'.format(
            name=self.name,
            model=model_meta_options._model_repr,
            choices=', '.join(f'{c!r}' for c in valid))
        assert value in valid, msg


class AbstractOption(ModelMetaOption):
    def __init__(self):
        super().__init__(name='abstract', default=False, inherit=False)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        if '__abstract__' in meta_args.clsdict:
            return True
        return super().get_value(meta, base_model_meta, meta_args)

    def contribute_to_class(self, meta_args: MutableMetaArgs, is_abstract,
                            model_meta_options):
        if is_abstract:
            meta_args.clsdict['__abstract__'] = True


class ModelMetaOptions:
    def __init__(self):
        self._meta_args: MutableMetaArgs = None

    def _get_model_meta_options(self) -> List[ModelMetaOption]:
        """"
        Define fields allowed in the Meta class on end-user models, and the
        behavior of each.

        Custom ModelMetaOptions classes should override this method to customize
        the options supported on class Meta of end-user models.
        """
        # when options require another option, its dependent must be listed.
        # options in this list are not order-dependent, except where noted.
        return [
            AbstractOption(),  # required; must be first
            ModelMetaOption('lazy_mapping', default=False, inherit=True),
            RelationshipsOption(),  # requires lazy_mapping

            BaseTablenameOption(),
            PolymorphicDiscriminatorColumn(),
            PolymorphicIdentityOption(),
            PolymorphicJoinedPkColumn(),
            PolymorphicOption(),  # must be after PolymorphicDiscriminatorColumn
                                  # requires BaseTablenameOption

            # all ModelColumnMetaOption subclasses require PolymorphicOption
            PrimaryKeyColumnOption(),  # must be after PolymorphicJoinedPkColumn
            CreatedAtColumnOption(),
            UpdatedAtColumnOption(),
        ]

    def _contribute_to_class(self, meta_args: MutableMetaArgs):
        self._meta_args = meta_args
        meta_args.clsdict['_meta'] = self

        meta = meta_args.clsdict.pop('Meta', None)
        base_model_meta = deep_getattr({}, meta_args.bases, '_meta', None)

        options = self._get_model_meta_options()
        if not isinstance(options[0], AbstractOption):
            raise Exception('The first option in _get_model_meta_options '
                            'must be an instance of AbstractOption')

        self._fill_from_meta(meta, base_model_meta)
        for option in options:
            option.contribute_to_class(meta_args,
                                       getattr(self, option.name), self)

    def _fill_from_meta(self, meta, base_model_meta):
        # Exclude private/protected fields from the meta
        meta_attrs = {} if not meta else {k: v for k, v in vars(meta).items()
                                          if not k.startswith('_')}

        for option in self._get_model_meta_options():
            assert not hasattr(self, option.name), \
                f"Can't override field {option.name}."
            value = option.get_value(meta, base_model_meta, self._meta_args)
            option.check_value(value, self)
            meta_attrs.pop(option.name, None)
            setattr(self, option.name, value)

        if meta_attrs:
            # Some attributes in the Meta aren't allowed here
            raise TypeError(
                f"'class Meta' for {self._model_repr!r} got unknown "
                f"attribute(s) {','.join(sorted(meta_attrs.keys()))}")

    @property
    def _is_base_model(self):
        base_meta = deep_getattr({}, self._meta_args.bases, '_meta')
        return base_meta.abstract

    @property
    def _model_repr(self):
        return self._meta_args._model_repr

    def __repr__(self):
        return '<{cls} model={model!r} model_meta_options={attrs!r}>'.format(
            cls=self.__class__.__name__,
            model=self._model_repr,
            attrs={option.name: getattr(self, option.name)
                   for option in self._get_model_meta_options()})


class SQLAlchemyBaseModelMeta(DefaultMeta):
    def __new__(mcs, name, bases, clsdict):
        meta_args = MutableMetaArgs(mcs, name, bases, clsdict)
        model_meta_options_class = deep_getattr(
            clsdict, bases, '_meta_options_class', ModelMetaOptions)
        model_meta_options: ModelMetaOptions = model_meta_options_class()
        model_meta_options._contribute_to_class(meta_args)

        if '__abstract__' in clsdict:
            return super().__new__(mcs, name, bases, clsdict)

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
        if self._should_convert_bases(meta_args):
            meta_args.bases = self._convert_bases_to_mixins(meta_args.bases)
        self._registry[meta_args.name][meta_args._module] = \
            MetaNewArgs(*meta_args)

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

    def _should_convert_bases(self, meta_args: MutableMetaArgs):
        if meta_args._model_meta_options.polymorphic:
            return False

        for b in meta_args.bases:
            if b.__name__ in self._registry:
                return True

        return meta_args.name in self._registry

    def _convert_bases_to_mixins(self, bases):
        """
        For each base class in bases that the _ModelRegistry knows about, create
        a replacement class containing the methods and attributes from the base
        class:
         - the mixin should only extend object (not db.Model)
         - if any of the attributes are MapperProperty instances (relationship,
           association_proxy, etc), then turn them into @declared_attr props
        """
        def _mixin_name(name):
            return f'{name}ConvertedMixin'

        new_bases = {}
        for b in reversed(bases):
            if b.__name__ not in self._registry:
                new_bases[b.__name__] = b
                continue

            _, base_name, base_bases, base_clsdict = \
                self._registry[b.__name__][b.__module__]

            for bb in reversed(base_bases):
                if (bb.__name__ not in new_bases
                        and _mixin_name(bb.__name__) not in new_bases):
                    new_bases[bb.__name__] = bb

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

            mixin_name = _mixin_name(base_name)
            new_bases[mixin_name] = type(mixin_name, (object,), clsdict)

        return tuple(reversed(list(new_bases.values())))


_model_registry = _ModelRegistry()
