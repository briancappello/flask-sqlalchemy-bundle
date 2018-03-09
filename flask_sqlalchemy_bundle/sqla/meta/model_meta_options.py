from flask_sqlalchemy.model import camel_to_snake_case
from sqlalchemy import func as sa_func, types as sa_types
from sqlalchemy.orm import RelationshipProperty

from ..column import Column
from ..relationships import foreign_key
from ..types import BigInteger, DateTime

from .types import MutableMetaArgs


class MetaOption:
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


class ColumnMetaOption(MetaOption):
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


class AbstractMetaOption(MetaOption):
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


class PrimaryKeyColumnMetaOption(ColumnMetaOption):
    def __init__(self, name='pk', default='id', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(BigInteger, primary_key=True)


class CreatedAtColumnMetaOption(ColumnMetaOption):
    def __init__(self, name='created_at', default='created_at', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(DateTime, server_default=sa_func.now())


class UpdatedAtColumnMetaOption(ColumnMetaOption):
    def __init__(self, name='updated_at', default='updated_at', inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)

    def get_column(self, model_meta_options):
        return Column(DateTime,
                      server_default=sa_func.now(), onupdate=sa_func.now())


class LazyMappedMetaOption(MetaOption):
    def __init__(self, name='lazy_mapped', default=False, inherit=True):
        super().__init__(name=name, default=default, inherit=inherit)


class RelationshipsMetaOption(MetaOption):
    def __init__(self):
        super().__init__('relationships', inherit=True)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        """overridden to merge with inherited value"""
        if meta_args._model_meta.abstract:
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
                    if v.backref and model_meta_options.lazy_mapped:
                        raise Exception(
                            f'Discovered a lazy-mapped backref `{k}` on '
                            f'`{meta_args._model_repr}`. Currently this '
                            'is unsupported; please use `db.relationship` with '
                            'the `back_populates` kwarg on both sides instead.')

        for base in meta_args.bases:
            discover_relationships(vars(base))
        discover_relationships(meta_args.clsdict)

        relationships.update(discovered_relationships)


class _TestingMetaOption(MetaOption):
    def __init__(self):
        super().__init__('_testing_', default=None, inherit=True)


class _BaseTablenameMetaOption(MetaOption):
    def __init__(self):
        super().__init__('_base_tablename', default=None, inherit=False)

    def get_value(self, meta, base_model_meta, meta_args: MutableMetaArgs):
        if base_model_meta and not base_model_meta.abstract:
            bm = base_model_meta._meta_args
            return bm.clsdict.get('__tablename__', camel_to_snake_case(bm.name))


class PolymorphicOnColumnMetaOption(ColumnMetaOption):
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


class PolymorphicJoinedPkColumnMetaOption(ColumnMetaOption):
    def __init__(self):
        # name, default, and inherited are all ignored for this option
        super().__init__(name='_', default='_')

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


class PolymorphicIdentityMetaOption(MetaOption):
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


class PolymorphicMetaOption(MetaOption):
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
