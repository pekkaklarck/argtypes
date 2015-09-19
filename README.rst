Decorator for argument type verification and conversion
=======================================================

This module provides ``argtypes`` decorator that can verify argument types
of Python functions and convert arguments to expected types. The main usage
is with `Robot Framework <http://robotframework.org>`_ test libraries that
want to verify/convert arguments their keywords accept.

Requires `wrapt <https://pypi.python.org/pypi/wrapt>`_ that can be installed
with::

    pip install wrapt

Examples
========

Basic argument type checking and conversion:

.. sourcecode:: python

    from argtypes import argtypes

    class MyClass(object):
        pass

    @argtypes(MyClass)
     def func(arg):
        assert isinstance(arg, MyClass)

    func(MyClass())

    @argtypes(int, arg2=str, arg3=bool)
    def func2(arg1, arg2, arg3=True):
        assert isinstance(arg1, int)
        assert isinstance(arg2, str)
        assert isinstance(arg3, bool)

    func2(42, 42)
    func2(arg1='1', arg2=2, arg3='False')

Registering custom converters:

.. sourcecode:: python

    from argtypes import argtypes

    class MyClass(object):
        def __init__(self, value):
            self.value = value

    @argtypes(MyClass)
    def func(arg):
        return arg

    argtypes.register_converter(MyClass)
    assert func(42).value == 42

    argtypes.register_converter(MyClass, lambda arg: MyClass(arg*2))
    assert func(42).value == 84

    argtypes.unregister_converter(MyClass)
