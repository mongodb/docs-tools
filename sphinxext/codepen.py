from docutils import nodes
from docutils.parsers.rst import Directive, directives


class codepen(nodes.Element):
    pass


def visit_codepen(self, node):
    slug = self.attval(node['slug'][0])
    attributes = {
        'data-pen-title': slug,
        'data-slug-hash': slug,
        'data-height': '600',
        'data-theme-id': '32535',
        'data-default-tab': 'js,result',
        'data-user': 'mongodb-docs',
        'data-embed-version': '2',
        'data-editable': 'true'
    }
    start_tag = self.starttag(node, 'p', CLASS='codepen', **attributes)
    self.body.append(start_tag)


def depart_codepen(self, node):
    slug = self.attval(node['slug'][0])
    link = 'https://codepen.io/mongodb-docs/pen/{slug}'.format(slug=slug)
    redirect = '''<a href="{link}">
        See this example on codepen: {slug}
    </a>'''.format(link=link, slug=slug)
    self.body.append('{redirect}</p>\n'.format(redirect=redirect))


class Codepen(Directive):
    """
    Embed a mongodb-docs codepen with the provided slug
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
    directives.register_directive('codepen', Codepen)

    return {
        'parallel_read_safe': False,
        'parallel_write_safe': True,
    }
