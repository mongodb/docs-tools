"""
Provides a simple, lightweight object used to capture data about an error
encountered while checking or validating a resource.
"""
import logging
import multiprocessing
import sys
import threading
import traceback

import giza.libgiza.config

logger = logging.getLogger('giza.libgiza.error')

if sys.version_info >= (3, 0):
    basestring = str

_DEFAULT_ERROR_MESSAGE = "generic error"


class Error(object):
    """
    Collects information about, and represents an error encountered. Use in
    situations where you want to track errors, but don't want to raise
    exceptions (e.g. for continue on error situations.)
    """

    def __init__(self, message=_DEFAULT_ERROR_MESSAGE, include_trace=True, fatal=True):
        self.capture_trace()
        self._include_trace = include_trace
        self._fatal = fatal
        self._payload = None
        self.message = message

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        if hasattr(self, "_message") and self._message != _DEFAULT_ERROR_MESSAGE:
            raise ValueError("cannot overwrite existing message ({0}) with new message "
                             "({1})".format(self._message, value))
        elif isinstance(value, basestring):
            self._message = value
        else:
            raise TypeError("error message should be a string. cannot set to: "
                            "{0} ({1})".format(value, type(value)))

    @property
    def fatal(self):
        if hasattr(self, "_fatal"):
            return self._fatal
        else:
            return True

    @fatal.setter
    def fatal(self, value):
        if isinstance(value, bool):
            self._fatal = value
        else:
            raise TypeError("fatal option must be a bool. ({0}, {1})".format(value, type(value)))

    @property
    def include_trace(self):
        if hasattr(self, "_include_trace"):
            return self._include_trace
        else:
            return True

    @include_trace.setter
    def include_trace(self, value):
        if isinstance(value, bool):
            self._include_trace = value
        else:
            raise TypeError("include_trace option must be a bool. "
                            "({0}, {1})".format(value, type(value)))

    @property
    def trace(self):
        # we want to drop the last stack frame because it's the assignment to
        # self._trace, which isn't relevant to the error.
        return self._trace[-10:][:-2]

    def capture_trace(self):
        self._trace = traceback.extract_stack()

    @property
    def payload(self):
        if isinstance(self._payload, dict):
            return self._payload
        elif isinstance(self._payload, giza.libgiza.config.ConfigurationBase):
            return self._payload.dict()
        else:
            return {}

    @payload.setter
    def payload(self, value):
        if isinstance(value, (dict, giza.libgiza.config.ConfigurationBase)):
            self._payload = value
        else:
            raise TypeError("error payloads must be dict subclasses or "
                            "giza.libgiza configuration objects, cannot set to: "
                            "{0} ({1})".format(value, type(value)))

    def render_output(self, prefix=""):
        output = []
        if self.fatal:
            output.append("encountered fatal error:")
        else:
            output.append("encountered non-fatal error:")

        output.append("    " + self.message)

        if self.include_trace:
            output.append("traceback:")
            for trace_line in traceback.format_list(self.trace):
                output.extend([ln for ln in trace_line.split("\n") if ln != ''])

        return prefix + ("\n" + prefix).join(output)

    def dict(self):
        return {"message": self.message,
                "payload": self.payload,
                "fatal": self.fatal,
                "trace": [{"file": t[0], "line": t[1], "function": t[2], "operation": t[3]}
                          for t in self.trace]}

    # define correct representations
    def __repr__(self):
        return str(self.dict())

    def __str__(self):
        return self.render_output()

    def __format__(self):
        return self.render_output()


class ErrorCollector(object):
    """
    A class that exists to collect and aggregate ErrorObject instances,
    potentially across threads or process pools.
    """

    def __init__(self, name="error-collector", concurrency_type="thread"):
        self._contains_fatal_error = False
        self.errors = []

        if concurrency_type.startswith("proc"):
            self.lock = multiprocessing.RLock()
        else:
            self.lock = threading.RLock()

        self.name = name

    def __len__(self):
        return len(self.errors)

    @property
    def fatal(self):
        with self.lock:
            return self._contains_fatal_error

    @property
    def count(self):
        with self.lock:
            return len(self.errors)

    @property
    def name(self):
        if hasattr(self, "_name"):
            return self._name
        else:
            return "error-collector"

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self._name = value
        else:
            raise TypeError("name option must be a string. "
                            "({0}, {1})".format(value, type(value)))

    def has_errors(self):
        if self.count > 0:
            return True
        else:
            return False

    def add(self, error):
        if error is None:
            return
        elif isinstance(error, Error):
            with self.lock:
                if error.fatal:
                    self._contains_fatal_error = True

                self.errors.append(error)
        elif isinstance(error, ErrorCollector):
            with self.lock:
                with error.lock:
                    if error.fatal:
                        self._contains_fatal_error = True
                    self.errors.extend(error.errors)
                    error.clear()
        else:
            raise TypeError("can only add ErrorObject and ErrorCollector objects to an "
                            "ErrorCollector. {0} ({1})".format(error, type(error)))

    def clear(self):
        if self.has_errors():
            logger.debug("clearing {0} errors from error group".format(self.count))

        with self.lock:
            self._contains_fatal_error = False
            self.errors = []

    def render_output(self, prefix=""):
        if not self.has_errors():
            return ""
        else:
            with self.lock:
                if self.fatal:
                    output = ["encountered {0} errors. (fatal):".format(self.count)]
                else:
                    output = ["encountered {0} errors:".format(self.count)]

                for num, error in enumerate(self.errors, start=1):
                    output.append("error: {0}".format(num))

                    if prefix == "":
                        output.append(error.render_output("    "))
                    else:
                        output.append(error.render_output(prefix))

                return prefix + ("\n" + prefix).join(output)

    def dict(self):
        if not self.has_errors():
            return {"errors": []}
        else:
            with self.lock:
                return {"errors": [e.dict() for e in self.errors]}

    # define correct representations
    def __repr__(self):
        return str(self.dict())

    def __str__(self):
        return self.render_output()

    def __format__(self):
        return self.render_output()

    def __bool__(self):
        return self.has_errors() and self.fatal

    def __nonzero__(self):
        # Python 2 compat
        return self.__bool__()
