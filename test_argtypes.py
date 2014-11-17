import unittest
import inspect

from argtypes import argtypes


class MyType(object):
    def __init__(self, value=None):
        self.value = value


@argtypes(MyType)
def function(arg):
    assert isinstance(arg, MyType)
    return arg


@argtypes(str, arg2=int, arg3=int)
def function2(arg1, arg2=2, **kwargs):
    assert isinstance(arg1, str)
    assert isinstance(arg2, int)
    assert int(arg1) * 2 == arg2
    assert kwargs.get('arg3', arg2) == arg2


@argtypes((int, str, dict), (int,))
def function3(arg1, arg2=2):
    assert arg1 in (1, '1') and arg2 == 2


@argtypes()
def function0():
    pass


class NewStyle(object):
    @argtypes(MyType, int)
    def method(self, foo, bar=42):
        assert isinstance(foo, MyType)
        assert abs(bar) == 42
    @argtypes()
    def no_args(self):
        pass
    def non_decorated(self, arg):
        pass


class OldStyle:
    @argtypes(MyType, int)
    def method(self, foo, bar=42):
        assert isinstance(foo, MyType)
        assert abs(bar) == 42
    @argtypes()
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
        NewStyle().method(MyType(), 42)
        NewStyle().method(bar=-42, foo=MyType())
        NewStyle().no_args()
        NewStyle().non_decorated(42)

    def test_method_in_old_style_class(self):
        OldStyle().method(MyType())
        OldStyle().method(MyType(), 42)
        OldStyle().method(bar=-42, foo=MyType())
        OldStyle().no_args()
        OldStyle().non_decorated(42)

    def test_argspec_is_preserved(self):
        self.assertEqual(inspect.getargspec(function),
                         (['arg'], None, None, None))
        self.assertEqual(inspect.getargspec(function2),
                         (['arg1', 'arg2'], None, 'kwargs', (2,)))
        self.assertEqual(inspect.getargspec(NewStyle().method),
                         (['self', 'foo', 'bar'], None, None, (42,)))
        self.assertEqual(inspect.getargspec(OldStyle().no_args),
                         (['self'], None, None, None))

    def test_kwarg_type_has_precedence_over_arg_type(self):
        # Specifying type as arg_type and kwarg_type could also be an error.
        @argtypes(str, arg=int)
        def func(arg):
            assert arg == 42
        func(42)
        func('42')
        func(arg=42)
        func(arg='42')

    def test_extra_types_are_allowed(self):
        # This could also be an error.
        @argtypes(str, int)
        def func(arg):
            assert arg == '42'
        func(42)
        func('42')
        func(arg=42)
        func(arg='42')


class InvalidArguments(unittest.TestCase):
    method = NewStyle().method

    def _verify_error(self, label, expected, actual, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except RuntimeError as error:
            self.assertEqual(str(error),
                             'Argument %s should have been <%s> but was <%s>.'
                             % (label, expected, actual))
        else:
            raise AssertionError('RuntimeError not raised')

    def test_defined_and_used_as_positional(self):
        self._verify_error('arg', 'MyType', 'int', function, 42)
        self._verify_error('foo', 'MyType', 'int', self.method, 42)

    def test_defined_as_positional_and_used_as_kwarg(self):
        self._verify_error('arg', 'MyType', 'int', function, arg=42)
        self._verify_error('foo', 'MyType', 'int', self.method, foo=42)

    def test_defined_as_kwarg_used_as_positional(self):
        self._verify_error('arg2', 'int', 'MyType', function2, 'xxx', MyType())
        self._verify_error('bar', 'int', 'tuple', self.method, MyType(), ())

    def test_defined_and_used_as_kwarg(self):
        self._verify_error('arg3', 'int', 'MyType', function2, 0, arg3=MyType())
        self._verify_error('bar', 'int', 'tuple', self.method, MyType(), bar=())

    def test_multiple_types(self):
        self._verify_error('arg1', 'int>, <str> or <dict', 'tuple', function3, ())
        self._verify_error('arg2', 'int', 'tuple', function3, 1, ())


class ArgumentTypeTypes(unittest.TestCase):

    def test_type_as_new_style_class(self):
        @argtypes(NewStyle)
        def func(arg):
            assert isinstance(arg, NewStyle)
        func(NewStyle())

    def test_type_as_old_style_class(self):
        @argtypes(OldStyle)
        def func(arg):
            assert isinstance(arg, OldStyle)
        func(OldStyle())

    def test_type_cannot_be_non_class(self):
        for invalid in MyType(), 42, (int, 1), ((), int), (None,):
            try:
                @argtypes(invalid)
                def func(arg):
                    pass
            except TypeError as error:
                self.assertEqual(str(error),
                                 'Argument type must be class, tuple of '
                                 'classes or None, got <%s> instance '
                                 'instead.' % type(invalid).__name__)
            else:
                raise AssertionError('TypeError not raised')

    def test_none_is_wildcard(self):
        @argtypes(None, int, a3=None)
        def func(a1, a2, a3=2):
            assert a1 * a2 == a3
        func(1, 2)
        func(1, 2, 2)
        func('a', 2, a3='aa')


class ArgumentConversion(unittest.TestCase):

    def test_base_types(self):
        for arg_type, arg_value in [(int, '1'), (long, '1'), (float, '3.14'),
                                    (bool, 'xxx'), (bool, ''),
                                    (str, 1), (unicode, True)]:
            @argtypes(arg_type)
            def func(arg):
                assert isinstance(arg, arg_type)
                return arg
            assert func(arg_value) == arg_type(arg_value)

    def test_bool_handles_false_as_string(self):
        @argtypes(bool, arg2=bool)
        def func(arg1, arg2=True):
            assert isinstance(arg1, bool)
            assert isinstance(arg2, bool)
            assert arg1 is not arg2
        func(False)
        func(True, False)
        func('non-empty', '')
        func('True', False)
        func('True', 'False')
        func('FALSE', 'TRUE')
        func('true', arg2='false')


class CustomConverter(unittest.TestCase):

    def tearDown(self):
        argtypes.unregister_converter(MyType)

    def test_type_itself(self):
        argtypes.register_converter(MyType)
        arg = function('Kekkonen')
        assert arg.value == 'Kekkonen'

    def test_function(self):
        argtypes.register_converter(MyType, lambda arg: MyType(arg*2))
        assert function('foo').value == 'foofoo'
        assert function(21).value == 42

    def test_return_different_type(self):
        @argtypes(MyType)
        def func(arg):
            return arg
        argtypes.register_converter(MyType, lambda arg: arg*2)
        assert func('foo') == 'foofoo'
        assert func(21) == 42

    def test_conversion_error(self):
        def positive(arg):
            arg = int(arg)
            if arg <= 0:
                raise ValueError
            return arg
        argtypes.register_converter(MyType, positive)
        @argtypes(MyType)
        def func(number):
            assert isinstance(number, int)
            assert number > 0
        func(1)
        func('2')
        self.assertRaises(ValueError, func, 'non a number')
        self.assertRaises(ValueError, func, -1)
        self.assertRaises(ValueError, func, '0')

    def test_type_as_tuple(self):
        argtypes.register_converter((int, float), lambda arg: float(arg))
        @argtypes((int, float))
        def func(arg):
            assert arg == 42
        func(42)
        func('42')

    def test_register_returns_old_value(self):
        converter = lambda arg: arg
        assert argtypes.register_converter(MyType) is None
        assert argtypes.register_converter(MyType, converter) is MyType
        assert argtypes.register_converter(MyType) is converter
        assert argtypes.register_converter(MyType) is MyType

    def test_unregister_returns_old_value(self):
        assert argtypes.unregister_converter(MyType) is None
        argtypes.register_converter(MyType)
        assert argtypes.unregister_converter(MyType) is MyType
        assert argtypes.unregister_converter(MyType) is None

    def test_registered_type_must_be_valid(self):
        for invalid in MyType(), 2, None, (int, 1), ((), int), (None,):
            try:
                argtypes.register_converter(invalid)
            except TypeError as error:
                self.assertEqual(str(error),
                                 'Argument type must be class or tuple of '
                                 'classes, got <%s> instance instead.'
                                 % type(invalid).__name__)
            else:
                raise AssertionError('TypeError not raised')


if __name__ == '__main__':
    unittest.main()
