import inspect
from types import ClassType, NoneType
from decorator import decorator


BASE_TYPES = [int, long, bool, float, str, unicode]


def arguments(*arg_types, **kwarg_types):
    validate_types(arg_types + tuple(kwarg_types.values()))
    @decorator
    def argument_handler(func, *args, **kwargs):
        if args and is_method(func, args[0]):
            local_arg_types = (None,) + arg_types
        else:
            local_arg_types = arg_types
        argspec = inspect.getargspec(func).args
        args = handle_args(args, argspec, local_arg_types, kwarg_types)
        kwargs = dict(handle_kwargs(kwargs, kwarg_types))
        return func(*args, **kwargs)
    return argument_handler


def validate_types(arg_types):
    for arg_type in arg_types:
        if not isinstance(arg_type, (type, ClassType, tuple, NoneType)):
            raise TypeError('Argument type must be class, tuple of classes or '
                            'None, got <{}> instance instead.'.format(
                            type(arg_type).__name__))

def handle_args(args, argspec, arg_types, kwarg_types):
    for index, arg in enumerate(args):
        if index < len(arg_types):
            arg = verify_argument(arg, arg_types[index], index+1)
        elif argspec[index] in kwarg_types:
            name = argspec[index]
            arg = verify_argument(arg, kwarg_types[name], name)
        yield arg

def handle_kwargs(kwargs, kwarg_types):
    for name, arg in kwargs.iteritems():
        if name in kwarg_types:
            arg = verify_argument(arg, kwarg_types[name], name)
        yield name, arg


def is_method(func, self):
    method = getattr(self, func.__name__, None)
    im_func = getattr(method, 'im_func', None)
    return getattr(im_func, 'undecorated', None) is func


def verify_argument(argument, expected_type, label):
    if expected_type is None or isinstance(argument, expected_type):
        return argument
    if expected_type in BASE_TYPES:
        try:
            return expected_type(argument)
        except TypeError:
            pass
    raise RuntimeError('Argument {} should have been {} but was <{}>.'.format(
        label, _format_expected(expected_type), type(argument).__name__))


def _format_expected(expected):
    if not isinstance(expected, tuple):
        expected = (expected,)
    expected = ['<{}>'.format(exp.__name__) for exp in expected]
    if len(expected) == 1:
        return expected[0]
    return '{} or {}'.format(', '.join(expected[:-1]), expected[-1])
