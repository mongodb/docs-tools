"""
A simple role for dynamically generating snippets of content.

Usage:
  :eval:`<python expression>`

The python expression has access to the following modules:
  * datetime
"""
import datetime
from docutils import nodes


def eval_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    text = str(eval(text, {
        'datetime': datetime
    }))

    node = nodes.Text(text)
    return [node], []


def setup(app):
    from docutils.parsers.rst import roles
    roles.register_local_role('eval', eval_role)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
