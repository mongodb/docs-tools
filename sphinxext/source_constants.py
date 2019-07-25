import re
import sys
import docutils.io

PAT_VARIABLE = re.compile(r'{\+([\w-]+)\+}')


def handle_match(app, docname, source, match):
    """Replace a given placeholder match with a value from the Sphinx
       configuration. Log a warning if it's not defined."""
    variable_name = match.group(1)
    try:
        return app.config.source_constants[variable_name]
    except KeyError:
        lineno = source.count('\n', 0, match.start())
        app.warn('{} not defined in conf.py'.format(variable_name), (docname, lineno))


def substitute_source(app, docname, source):
    """Substitute all placeholders within a string."""
    return PAT_VARIABLE.sub(lambda match: handle_match(app, docname, source, match), source)


def handle_source_read(app, docname, source):
    """source-read event handler to substitute placeholders from root
       source files."""
    source[0] = substitute_source(app, docname, source[0])


def setup(app):
    class FileInput(docutils.io.FileInput):
        """Subclass of the docutils FileInput class which replaces constant
           placeholders with values from the Sphinx configuration."""
        def read(self):
            """Read and decode a single file and return the data (Unicode string)."""
            try:
                if self.source is sys.stdin and sys.version_info >= (3, 0):
                    # read as binary data to circumvent auto-decoding
                    data = self.source.buffer.read()
                    # normalize newlines
                    data = b'\n'.join(data.splitlines()) + b'\n'
                else:
                    data = self.source.read()
            except (UnicodeError, LookupError):  # (in Py3k read() decodes)
                if not self.encoding and self.source_path:
                    # re-read in binary mode and decode with heuristics
                    b_source = open(self.source_path, 'rb')
                    data = b_source.read()
                    b_source.close()
                    # normalize newlines
                    data = b'\n'.join(data.splitlines()) + b'\n'
                else:
                    raise
            finally:
                if self.autoclose:
                    self.close()

            return substitute_source(app, self.source_path, self.decode(data))

    # Handle included .rst files
    docutils.io.FileInput = FileInput
    # Handle .txt files
    app.connect('source-read', handle_source_read)

    app.add_config_value('source_constants', {}, 'env')

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
