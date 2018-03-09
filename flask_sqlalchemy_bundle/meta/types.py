from collections import namedtuple


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
    def _model_meta(self):
        return self.clsdict['_meta']

    def __iter__(self):
        return iter([self.mcs, self.name, self.bases, self.clsdict])

    def __repr__(self):
        return f'<MutableMetaArgs model={self._model_repr}>'
