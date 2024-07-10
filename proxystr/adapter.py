from pydantic_core import core_schema


class _ExtraTypeConstructor(type):
    def __new__(cls, name, bases, dct):
        new_class = super().__new__(cls, name, bases + (_ExtraTypeAdapter,), dct)

        if '__new__' not in dct:
            new_class.__new__ = _ExtraTypeAdapter.__new__
        return new_class


class _ExtraTypeAdapter:
    """Нельзя наследоваться напрямую, - это класс-примесь"""

    def __new__(cls, v, *args, **kwargs):
        return cls.validate(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source, handler):
        return core_schema.no_info_after_validator_function(
            cls.validate, handler(cls.__bases__[0]))

    @classmethod
    def __get_pydantic_json_schema__(cls, _source, handler):
        return handler(cls.__bases__[0])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        raise NotImplementedError('"validate" method must be implemented and must return a value')
