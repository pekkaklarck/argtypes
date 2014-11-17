import inspect
from types import ClassType, NoneType
from wrapt import decorator


class arguments(object):
    _converters = {
        int: int, long: long, float: float, str: str, unicode: unicode,
        bool: lambda arg: bool(arg.upper() not in ('FALSE', '')
                               if isinstance(arg, (str, unicode)) else arg)
    }

    def __init__(self, *arg_types, **kwarg_types):
        self._validate_types(arg_types + tuple(kwarg_types.values()))
        self._arg_types = arg_types
        self._kwarg_types = kwarg_types

    @classmethod
    def _validate_types(cls, arg_types):
        for arg_type in arg_types:
            if not isinstance(arg_type, (type, ClassType, tuple, NoneType)):
                raise TypeError('Argument type must be class, tuple of classes '
                                'or None, got <%s> instance instead.'
                                % type(arg_type).__name__)

    @classmethod
    def register_converter(cls, arg_type, converter=None):
        cls._validate_types([arg_type])
        old = cls._converters.get(arg_type)
        cls._converters[arg_type] = converter or arg_type
        return old

    @classmethod
    def unregister_converter(cls, arg_type):
        if arg_type in cls._converters:
            return cls._converters.pop(arg_type)

    @decorator
    def __call__(self, wrapped, instance, args, kwargs):
        argspec = inspect.getargspec(wrapped).args
        if instance:
            argspec.pop(0)    # drop self
        args = tuple(self._handle_args(args, argspec))
        kwargs = dict(self._handle_kwargs(kwargs, argspec))
        return wrapped(*args, **kwargs)

    def _handle_args(self, args, argspec):
        type_count = len(self._arg_types)
        for index, arg in enumerate(args):
            name = argspec[index]
            if name in self._kwarg_types:
                arg = self._handle_arg(arg, self._kwarg_types[name], name)
            elif index < type_count:
                arg = self._handle_arg(arg, self._arg_types[index], name)
            yield arg

    def _handle_kwargs(self, kwargs, argspec):
        type_count = len(self._arg_types)
        for name, arg in kwargs.iteritems():
            if name in self._kwarg_types:
                arg = self._handle_arg(arg, self._kwarg_types[name], name)
            elif name in argspec:
                index = argspec.index(name)
                if index < type_count:
                    arg = self._handle_arg(arg, self._arg_types[index], name)
            yield name, arg

    def _handle_arg(self, argument, expected_type, label):
        if expected_type is None or isinstance(argument, expected_type):
            return argument
        if expected_type in self._converters:
            converter = self._converters[expected_type]
            try:
                return converter(argument)
            except TypeError:
                pass
        raise RuntimeError('Argument %s should have been %s but was <%s>.'
                           % (label, self._format_expected(expected_type),
                              type(argument).__name__))

    def _format_expected(self, expected):
        if not isinstance(expected, tuple):
            expected = (expected,)
        expected = ['<%s>' % exp.__name__ for exp in expected]
        if len(expected) == 1:
            return expected[0]
        return '%s or %s' % (', '.join(expected[:-1]), expected[-1])
