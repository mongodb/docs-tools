import re
from docutils import nodes
from docutils.parsers.rst import roles
from sphinx.util.nodes import split_explicit_title

PAT_STRIP = re.compile(r'-(?:o|(?:alt))$')

# A pre-approved list of icons. Approval required to add to this list.
# Make sure you update the documentation in github.com:mongodb/docs-meta
# as well when updating.
ICONS = set([
    'caret-right',
    'caret-square-left',
    'caret-square-right',
    'check-circle',
    'check-square',
    'edit',
    'exclamation-circle',
    'pencil',
    'save',
    'trash',
    'trash-alt'
])


def class_to_label(css_class):
    """Approximate a label for screen readers from a FontAwesome class."""
    return PAT_STRIP.sub('', css_class).replace('-', ' ') + ' icon'


class IconNode(nodes.General, nodes.Inline, nodes.Element):
    @staticmethod
    def visit_icon(self, node):
        # I've tested this in Safari w/ macOS Voiceover
        self.body.append(
            self.starttag(
                node,
                'span',
                CLASS='fa fa-{}'.format(node['css_class']),
                **{'title': node['label']}))
        self.body.append(self.starttag(node, 'span', CLASS='screenreader'))
        self.body.append(node['label'])

    @staticmethod
    def depart_icon(self, node=None):
        self.body.append('</span></span>\n')


def icon_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
    errors = []
    has_explicit_title, label, css_class = split_explicit_title(text)
    if css_class not in ICONS:
        errors.append(inliner.reporter.error('Unknown icon: ' + css_class, line=lineno))

    label = label if has_explicit_title else class_to_label(css_class)

    config = inliner.document.settings.env.config
    if config._raw_config['tags'].eval_condition('html'):
        return [IconNode(css_class=css_class, label=label)], []

    return [nodes.Text(label)], errors


def setup(app):
    app.add_node(IconNode, html=(IconNode.visit_icon, IconNode.depart_icon))
    roles.register_local_role('icon', icon_role)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
