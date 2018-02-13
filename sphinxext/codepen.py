import logging
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.directives.code import CodeBlock
import inspect
import copy

logger = logging.getLogger('fasthtml')


class codepen(nodes.Element):
    pass


def visit_codepen(self, node):
    slug = node['slug'][0]
    script = '''<script src="https://production-assets.codepen.io/assets/embed/ei.js"></script>'''
    start_tag = '''<p
        class='codepen'
        data-pen-title={slug}
        data-slug-hash={slug}
        data-height="600"
        data-theme-id="32535"
        data-default-tab="js,result"
        data-user="mongodb-docs"
        data-embed-version="2"
        data-editable="true"
    >'''.format(slug=slug)
    # start_tag = self.starttag(
    #     node,
    #     'p',
    #     CLASS='codepen',
    #     data-pen-title=slug,
    #     data-slug-hash=slug,
    #     data-height="600",
    #     data-theme-id="32499",
    #     data-default-tab="js,result",
    #     data-user="mongodb-docs",
    #     data-embed-version="2",
    #     data-editable="true"
    # )
    self.body.append(script)
    self.body.append(start_tag)


def depart_codepen(self, node):
    self.body.append('CODEPEN HERE</p>\n')


class Codepen(Directive):
    """
    Embed a codepen with the provided slug
    """
    has_content = False
    required_arguments = 1
    optional_arguments = 0

    def run(self):

        pen = codepen('')
        pen['slug'] = [self.arguments[0]]
        return [pen]


def setup(app):
    app.add_node(codepen, html=(
        visit_codepen, depart_codepen
    ))
    app.add_directive('codepen', Codepen)
    directives.register_directive('codepen', Codepen)

    return {
        'parallel_read_safe': False,
        'parallel_write_safe': True,
    }
