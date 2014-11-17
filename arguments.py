import inspect
from types import ClassType, NoneType
from wrapt import decorator

BASE_TYPES = [int, long, bool, float, str, unicode]


class arguments(object):

    def __init__(self, *arg_types, **kwarg_types):
        self._validate_types(arg_types + tuple(kwarg_types.values()))
        self.arg_types = arg_types
        self.kwarg_types = kwarg_types

    def _validate_types(self, arg_types):
        for arg_type in arg_types:
            if not isinstance(arg_type, (type, ClassType, tuple, NoneType)):
                raise TypeError('Argument type must be class, tuple of classes '
                                'or None, got <%s> instance instead.'
                                % type(arg_type).__name__)

    @decorator
    def __call__(self, wrapped, instance, args, kwargs):
        argspec = inspect.getargspec(wrapped).args
        args = self._handle_args(args, argspec)
        kwargs = dict(self._handle_kwargs(kwargs))
        return wrapped(*args, **kwargs)

    def _handle_args(self, args, argspec):
        for index, arg in enumerate(args):
            if index < len(self.arg_types):
                arg = self._handle_arg(arg, self.arg_types[index], index+1)
            elif argspec[index] in self.kwarg_types:
                name = argspec[index]
                arg = self._handle_arg(arg, self.kwarg_types[name], name)
            yield arg

    def _handle_kwargs(self, kwargs):
        for name, arg in kwargs.iteritems():
            if name in self.kwarg_types:
                arg = self._handle_arg(arg, self.kwarg_types[name], name)
            yield name, arg

    def _handle_arg(self, argument, expected_type, label):
        if expected_type is None or isinstance(argument, expected_type):
            return argument
        if expected_type in BASE_TYPES:
            try:
                return expected_type(argument)
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
