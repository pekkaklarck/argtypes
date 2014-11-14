import inspect
import pytest



from arguments import arguments


class MyClass(object):
    pass


@arguments(MyClass)
def function(arg):
    return arg

@arguments(arg2=int, arg3=bool)
def function2(arg1, arg2=2, **kwargs):
    assert arg1 * 2 == arg2
    assert kwargs.get('arg3', True) is True


def _verify_error(exception, expected, actual, label=1):
    msg = 'Argument {} should have been <{}> but was <{}>.'.format(
        label, expected.__name__, actual.__name__)
    assert msg in str(exception)


def test_valid_arguments():
    arg = MyClass()
    assert function(arg) is arg
    function2(1, 2)
    function2(arg2=2, arg1=1, arg3=True)

def test_invalid_argument():
    with pytest.raises(RuntimeError) as exc:
        function(42)
    _verify_error(exc.value, MyClass, int)

def test_invalid_argument_defined_as_kwarg():
    with pytest.raises(RuntimeError) as exc:
        function2('non', 'ints')
    _verify_error(exc.value, int, str, label=2)

def test_invalid_kwarg():
    with pytest.raises(RuntimeError) as exc:
        function2('should be bool', arg3=MyClass())
    _verify_error(exc.value, bool, MyClass, label='arg3')


def test_convert_to_base_types():
    for type, input in [(int, '1'), (long, '1'), (float, '3.14'),
                        (bool, 'True'), (str, 1), (unicode, True)]:
        @arguments(type)
        def func(arg):
            return arg
        assert func(input) == type(input)


def test_argspec():
    assert inspect.getargspec(function) == (['arg'], None, None, None)
