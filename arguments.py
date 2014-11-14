import inspect
from decorator import decorator


def arguments(*arg_types, **kwarg_types):
    @decorator
    def deco(func, *args, **kwargs):
        if args and is_method(func, args[0]):
            local_arg_types = (None,) + arg_types
        else:
            local_arg_types = arg_types
        for index, (arg, expected) in enumerate(zip(args, local_arg_types)):
            verify_argument(arg, expected, index+1)
        for name, expected in kwarg_types.iteritems():
            if name in kwargs:
                verify_argument(kwargs[name], expected, name)
            else:
                argspec = inspect.getargspec(func).args
                if name in argspec:
                    index = argspec.index(name)
                    verify_argument(args[index], expected, index+1)
        return func(*args, **kwargs)
    return deco


def is_method(func, self):
    for name in dir(self):
        if name == func.__name__:
            attr = getattr(self, name)
            im_func = getattr(attr, 'im_func', None)
            if getattr(im_func, 'undecorated', None) is func:
                return True
    return False


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
