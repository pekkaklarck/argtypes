import unittest
import inspect

from arguments import arguments


class MyType(object):
    pass


@arguments(MyType)
def function(arg):
    assert isinstance(arg, MyType)
    return arg


@arguments(arg2=int, arg3=int)
def function2(arg1, arg2=2, **kwargs):
    assert isinstance(arg2, int)
    assert arg1 * 2 == arg2
    assert kwargs.get('arg3', arg2) == arg2


@arguments((int, str, dict), (int,))
def function3(arg1, arg2=2):
    assert arg1 in (1, '1') and arg2 == 2


@arguments()
def function0():
    pass


class NewStyle(object):
    @arguments(MyType, bool)
    def method(self, foo, bar=True):
        pass
    @arguments()
    def no_args(self):
        pass
    def non_decorated(self, arg):
        pass


class OldStyle:
    @arguments(MyType, bool)
    def method(self, foo, bar=True):
        pass
    @arguments()
    def no_args(self):
        pass
    def non_decorated(self, arg):
        pass


class ValidArguments(unittest.TestCase):

    def test_positional(self):
        arg = MyType()
        assert function(arg) is arg
        function2(1, 2)

    def test_named(self):
        function2(arg2=2, arg1=1, arg3=2)

    def test_multiple_types(self):
        function3(1)
        function3('1')
        function3('1', 2)
        function3(arg2=2, arg1=1)

    def test_no_arguments(self):
        function0()

    def test_method_in_new_style_class(self):
        NewStyle().method(MyType())
        NewStyle().method(MyType(), True)
        NewStyle().method(bar=False, foo=MyType())
        NewStyle().no_args()
        NewStyle().non_decorated(42)

    def test_method_in_old_style_class(self):
        OldStyle().method(MyType())
        OldStyle().method(MyType(), True)
        OldStyle().method(bar=False, foo=MyType())
        OldStyle().no_args()
        OldStyle().non_decorated(42)

    def test_argspec_is_preserved(self):
        self.assertEqual(inspect.getargspec(function),
                         (['arg'], None, None, None))
        self.assertEqual(inspect.getargspec(function2),
                         (['arg1', 'arg2'], None, 'kwargs', (2,)))
        self.assertEqual(inspect.getargspec(NewStyle().method),
                         (['self', 'foo', 'bar'], None, None, (True,)))
        self.assertEqual(inspect.getargspec(OldStyle().no_args),
                         (['self'], None, None, None))

    def test_kwarg_type_has_precedence_over_arg_type(self):
        # Specifying type as arg_type and kwarg_type could also be an error.
        @arguments(str, arg=int)
        def func(arg):
            assert arg == 42
        func(42)
        func('42')
        func(arg=42)
        func(arg='42')

    def test_extra_types_are_allowed(self):
        # This could also be an error.
        @arguments(str, int)
        def func(arg):
            assert arg == '42'
        func(42)
        func('42')
        func(arg=42)
        func(arg='42')


class InvalidArguments(unittest.TestCase):

    def _verify_error(self, label, expected, actual, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except RuntimeError, exception:
            self.assertEqual(str(exception),
                             'Argument %s should have been <%s> but was <%s>.'
                             % (label, expected, actual))
        else:
            raise AssertionError('RuntimeError not raised')

    def test_defined_and_used_as_positional(self):
        self._verify_error(1, 'MyType', 'int', function, 42)

    def test_defined_as_positional_and_used_as_kwarg(self):
        self._verify_error('arg', 'MyType', 'int', function, arg=42)

    def test_defined_as_kwarg_used_as_positional(self):
        self._verify_error('arg2', 'int', 'MyType',
                           function2, 'whatever', MyType())

    def test_defined_and_used_as_kwarg(self):
        self._verify_error('arg3', 'int', 'MyType',
                           function2, 1234, arg3=MyType())

    def test_multiple_types(self):
        self._verify_error(1, 'int>, <str> or <dict', 'tuple', function3, ())
        self._verify_error(2, 'int', 'tuple', function3, 1, ())


class ArgumentTypeTypes(unittest.TestCase):

    def test_type_as_new_style_class(self):
        @arguments(NewStyle)
        def func(arg):
            assert isinstance(arg, NewStyle)
        func(NewStyle())

    def test_type_as_old_style_class(self):
        @arguments(OldStyle)
        def func(arg):
            assert isinstance(arg, OldStyle)
        func(OldStyle())

    def test_type_cannot_be_non_class(self):
        try:
            @arguments(MyType())
            def func(arg):
                pass
        except TypeError, err:
            self.assertEqual(str(err), 'Argument type must be class, tuple of '
                             'classes or None, got <MyType> instance instead.')
        else:
            raise AssertionError('TypeError not raised')

    def test_none_is_wildcard(self):
        @arguments(None, int, a3=None)
        def func(a1, a2, a3=2):
            assert a1 * a2 == a3
        func(1, 2)
        func(1, 2, 2)
        func('a', 2, a3='aa')


class TestArgumentConversion(unittest.TestCase):

    def test_base_types(self):
        for arg_type, input in [(int, '1'), (long, '1'), (float, '3.14'),
                                (bool, 'xxx'), (str, 1), (unicode, True)]:
            @arguments(arg_type)
            def func(arg):
                assert isinstance(arg, arg_type)
                return arg
            assert func(input) == arg_type(input)


if __name__ == '__main__':
    unittest.main()
