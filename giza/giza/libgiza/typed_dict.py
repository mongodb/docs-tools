"""
Provides the basis for a more strictly typed dictionary that ensures all keys
and values will be of a specific type, and will throw exceptions if keys,
values, or pairs of keys and values are of the wrong type or fail validation.
"""

import abc
import future.utils
import logging

import giza.libgiza.error

logger = logging.getLogger('giza.libgiza.typed_dict')


class TypedDict(future.utils.with_metaclass(abc.ABCMeta, dict)):
    """
    An abstract base class definition that ensures that keys and values are of
    the correct type. Requires users implement ``check_key()``,
    ``check_value()`` and ``check_pair()`` methods that allow the these objects
    to validate input.
    """

    def __init__(self, key_type, value_type):
        errors = giza.libgiza.error.ErrorCollector()
        if isinstance(key_type, type):
            self.key_type = key_type
        else:
            errors.add(giza.libgiza.error.Error(
                message="key_type ({0}) is not a type value".format(key_type)))

        if isinstance(value_type, type):
            self.value_type = value_type
        else:
            errors.add(giza.libgiza.error.Error(
                "value_type ({0}) is not a type value".format(value_type)))

        if errors.has_errors() and errors.fatal:
            logger.debug(errors.render_output())
            raise TypeError(errors.dict())

    def __setitem__(self, key, value):
        type_errors = giza.libgiza.error.ErrorCollector()
        value_errors = giza.libgiza.error.ErrorCollector()

        if isinstance(key, self.key_type):
            value_errors.add(self.check_key(key))
        else:
            try:
                key = self.key_type(key)
            except Exception as e:
                type_errors.add(giza.libgiza.error.ErrorCollector(
                    message=("key {0} ({1}) is not of type {2} (had error "
                             "{3}:{4})").format(key, type(key), self.key_type, type(e), e)))

        if isinstance(value, self.value_type):
            value_errors.add(self.check_value(value))
        else:
            try:
                value = self.value_type(value)
            except Exception as e:
                type_errors.add(giza.libgiza.error.ErrorCollector(
                    message=("value for key {0} is not of type {1} (is {2}). (had error "
                             "{3}:{4})").format(key, self.value_type, type(value), type(e), e)))

        # if checks for pair errors depend on type/values being correct they
        # may except in unpredictable ways
        try:
            value_errors.add(self.check_pair(key, value))
        except Exception as e:
            value_errors.add(giza.libgiza.error.Error(
                message=("encountered {0} error when validating "
                         "pair for key {1}").format(type(e), key)))

        if type_errors.has_errors() and type_errors.fatal:
            logger.debug(type_errors.render_output())
            if value_errors.has_errors():
                logger.debug(value_errors.render_output())
            raise TypeError(type_errors.dict())

        if value_errors.has_errors() and value_errors.fatal:
            logger.debug(value_errors.render_output())
            raise ValueError(value_errors.dict())

        dict.__setitem__(self, key, value)

    def ingest(self, args):
        if args is None or len(args) == 0:
            return
        elif isinstance(args, tuple):
            dict.__init__(self, *args)
        else:
            dict.__init__(self, args)

    @abc.abstractmethod
    def check_key(self, key):
        return giza.libgiza.error.ErrorCollector()

    @abc.abstractmethod
    def check_value(self, value):
        return giza.libgiza.error.ErrorCollector()

    @abc.abstractmethod
    def check_pair(self, key, value):
        return giza.libgiza.error.ErrorCollector()
