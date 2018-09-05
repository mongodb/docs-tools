"""
A role allowing use of XML to create nested formatting.

Supported tags:
  - <mono>
  - <strong>
  - <em>
  - <ref target=[ref]>
    - Uses the :ref: role.
  - <link target=[url]>
    - Links to a specific URL.

Usage:
  :xml:`<strong>A link to our binary bson dump docs <mono><ref target="binary-bson-dumps">a link</ref></mono></strong>.
"""

from docutils import nodes
from docutils.parsers.rst import roles

import xml.sax
import xml.sax.handler


class RoleWrapper:
    __slots__ = ('domain_name', 'name')

    def __init__(self, domain_name, name):
        self.domain_name = domain_name
        self.name = name

    def get_role(self, domain):
        role = domain.roles.get(self.name, None)

        if role is None:
            role = roles._roles[self.name]

        return role


class LinkWrapper(RoleWrapper):
    def __call__(self, attrs, children, args):
        inliner = args[1]
        domain = inliner.document.settings.env.domains.get(self.domain_name)
        target = attrs['target']
        rawsource = ':{}:`{}`'.format(self.name, target)
        node = self.get_role(domain)(self.name, rawsource, target, *args)[0][0]

        if children:
            # Set up our children, and prevent delayed link resolution
            # (like intermanual) from trampling over them.
            node.children = children
            for child in children:
                child.parent = node
            node['refexplicit'] = True

        # Allow intermanual links to work
        node['refdomain'] = self.domain_name
        node['reftype'] = self.name

        return node


def make_node_wrapper(node):
    def inner(attrs, children, args):
        return node('', '', *children)

    return inner


class Handler(xml.sax.handler.ContentHandler, xml.sax.handler.ErrorHandler):
    ELEMENTS = {
        'strong': make_node_wrapper(nodes.strong),
        'em': make_node_wrapper(nodes.emphasis),
        'mono': make_node_wrapper(nodes.literal),
        'ref': LinkWrapper('std', 'ref'),
        'link': lambda attrs, children, args: nodes.reference('', '', *children, refuri=attrs.get('target', '#'))
    }

    def __init__(self, args):
        self.stack = []
        self.nodes = []
        self.errors = []

        self.args = args

    def startElement(self, name, attrs):
        self.stack.append((name, attrs, []))

    def endElement(self, name):
        element = self.stack.pop()
        el_name, el_attrs, el_nodes = element
        assert name == el_name

        new_node = self.ELEMENTS[name](el_attrs, el_nodes, self.args)
        if self.stack:
            self.stack[-1][2].append(new_node)
        else:
            self.nodes = [new_node]

    def characters(self, content):
        self.stack[-1][2].append(nodes.Text(content))

    def error(self, exception):
        self.errors.append(exception)

    def fatalError(self, exception):
        self.errors.append(exception)

    def warning(self, exception):
        self.errors.append(exception)


def xml_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    handler = Handler((lineno, inliner, options, content))
    xml.sax.parseString(text, handler, errorHandler=handler)

    if handler.errors:
        msg = inliner.reporter.error('XML parsing errors: ' + str(handler.errors),
                                     line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    return handler.nodes, []


def setup(app):
    roles.register_local_role('xml', xml_role)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
