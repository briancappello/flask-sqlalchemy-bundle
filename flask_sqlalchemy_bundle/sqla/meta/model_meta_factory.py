import os
from flask_unchained.constants import TEST
from typing import *

from .model_meta_options import (
    MetaOption,
    AbstractMetaOption,
    LazyMappedMetaOption,
    RelationshipsMetaOption,
    _BaseTablenameMetaOption,
    PolymorphicOnColumnMetaOption,
    PolymorphicIdentityMetaOption,
    PolymorphicJoinedPkColumnMetaOption,
    PolymorphicMetaOption,
    PrimaryKeyColumnMetaOption,
    CreatedAtColumnMetaOption,
    UpdatedAtColumnMetaOption,
    _TestingMetaOption,
)
from .types import MutableMetaArgs
from .utils import deep_getattr


class ModelMetaFactory:
    def __init__(self):
        self._meta_args: MutableMetaArgs = None

    def _get_model_meta_options(self) -> List[MetaOption]:
        """"
        Define fields allowed in the Meta class on end-user models, and the
        behavior of each.

        Custom ModelMetaOptions classes should override this method to customize
        the options supported on class Meta of end-user models.
        """
        # we can't use current_app to determine if we're under test, because it
        # doesn't exist yet
        testing_options = ([] if os.getenv('FLASK_ENV', False) != TEST
                           else [_TestingMetaOption()])

        # when options require another option, its dependent must be listed.
        # options in this list are not order-dependent, except where noted.
        # all ColumnMetaOptions subclasses require PolymorphicMetaOption
        return testing_options + [
            AbstractMetaOption(),  # required; must be first
            LazyMappedMetaOption(),
            RelationshipsMetaOption(),  # requires lazy_mapped

            PolymorphicMetaOption(),
            PolymorphicOnColumnMetaOption(),
            PolymorphicIdentityMetaOption(),
            PolymorphicJoinedPkColumnMetaOption(),  # requires _BaseTablename
            _BaseTablenameMetaOption(),

            # must be after PolymorphicJoinedPkColumnMetaOption
            PrimaryKeyColumnMetaOption(),
            CreatedAtColumnMetaOption(),
            UpdatedAtColumnMetaOption(),
        ]

    def _contribute_to_class(self, meta_args: MutableMetaArgs):
        self._meta_args = meta_args

        meta = meta_args.clsdict.pop('Meta', None)
        base_model_meta = deep_getattr(
            meta_args.clsdict, meta_args.bases, '_meta', None)

        meta_args.clsdict['_meta'] = self

        options = self._get_model_meta_options()
        if (os.getenv('FLASK_ENV', None) != TEST
                and not isinstance(options[0], AbstractMetaOption)):
            raise Exception('The first option in _get_model_meta_options '
                            'must be an instance of AbstractMetaOption')

        self._fill_from_meta(meta, base_model_meta)
        for option in options:
            option.contribute_to_class(meta_args,
                                       getattr(self, option.name, None), self)

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
            if option.name != '_':
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
            attrs={option.name: getattr(self, option.name, None)
                   for option in self._get_model_meta_options()})
