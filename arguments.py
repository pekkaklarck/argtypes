from inspect import getargspec
from decorator import decorator


def arguments(*arg_types, **kwarg_types):
    @decorator
    def deco(method, *args, **kwargs):
        for index, (arg, expected) in enumerate(zip(args, arg_types)):
            verify_argument(arg, expected, index+1)
        for name, expected in kwarg_types.iteritems():
            if name in kwargs:
                verify_argument(kwargs[name], expected, name)
            else:
                argspec = getargspec(method).args
                if name in argspec:
                    index = argspec.index(name)
                    verify_argument(args[index], expected, index+1)
        return method(*args, **kwargs)
    return deco


def verify_argument(argument, expected_type, label):
    if expected_type is None or isinstance(argument, expected_type):
        return argument
    raise RuntimeError('Argument {} should have been {} but was <{}>.'.format(
        label, _format_expected(expected_type), type(argument).__name__))


def _format_expected(expected):
    if not isinstance(expected, tuple):
        expected = (expected,)
    expected = ['<{}>'.format(exp.__name__) for exp in expected]
    if len(expected) == 1:
        return expected[0]
    return '{} or {}'.format(', '.join(expected[:-1]), expected[-1])
