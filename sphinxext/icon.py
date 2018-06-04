from docutils import nodes
from docutils.parsers.rst import roles
from sphinx.util.nodes import split_explicit_title


def class_to_label(css_class):
    """Approximate a label for screen readers from a FontAwesome class."""
    return css_class.rstrip('-o').replace('-', ' ') + ' icon'


class IconNode(nodes.General, nodes.Element):
    def __init__(self, css_class, label):
        super(IconNode, self).__init__()
        self.css_class = css_class
        self.label = label

    @staticmethod
    def visit_icon(self, node):
        # I've tested this in Safari w/ macOS Voiceover
        self.body.append(
            self.starttag(
                node,
                'span',
                CLASS='fa fa-{}'.format(node.css_class),
                **{'title': node.label}))
        self.body.append(self.starttag(node, 'span', CLASS='screenreader'))
        self.body.append(node.label)

    @staticmethod
    def depart_icon(self, node=None):
        self.body.append('</span></span>\n')


def icon_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    has_explicit_title, label, target = split_explicit_title(text)
    css_class = target

    label = label if has_explicit_title else class_to_label(css_class)

    config = inliner.document.settings.env.config
    if config._raw_config['tags'].eval_condition('html'):
        return [IconNode(css_class, label)], []

    return [nodes.Text(label)], []


def setup(app):
    app.add_node(IconNode, html=(IconNode.visit_icon, IconNode.depart_icon))
    roles.register_local_role('icon', icon_role)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
