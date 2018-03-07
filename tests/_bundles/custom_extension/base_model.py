from flask_sqlalchemy import Model as BaseModel
from flask_sqlalchemy_bundle.sqla.meta import MetaOption, ModelMetaFactory


class ExtendExisting(MetaOption):
    def __init__(self):
        super().__init__(name='extend_existing', default=True, inherit=False)

    def check_value(self, value, model_meta_options):
        msg = f'{self.name} Meta option on {model_meta_options._model_repr} ' \
              f'must be True or False'
        assert isinstance(value, bool), msg

    def contribute_to_class(self, meta_args, value, model_meta_options):
        if not value:
            return

        table_args = meta_args.clsdict.get('__table_args__', {})
        table_args['extend_existing'] = True
        meta_args.clsdict['__table_args__'] = table_args


class CustomModelMetaOptions(ModelMetaFactory):
    def _get_model_meta_options(self):
        return super()._get_model_meta_options() + [
            ExtendExisting(),
        ]


class Model(BaseModel):
    _meta_options_class = CustomModelMetaOptions

    class Meta:
        abstract = True
        extend_existing = True
