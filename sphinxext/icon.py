import collections
import re
import fett
from docutils import nodes, statemachine
from docutils.parsers.rst import roles, Directive
from sphinx.util.nodes import split_explicit_title
from docutils.utils.error_reporting import ErrorString

PAT_STRIP = re.compile(r'-(?:o|(?:alt))$')
ALL_SUFFIXES = ('-add', '-edit', '-exclamation', '-remove', '-restart')
HELP_TEMPLATE = fett.Template('''
.. list-table::

{{ for name in icons }}
   * - ``{{ name }}``
     - :{{ role }}:`{{ name }}`
{{ end }}
''')
IconSet = collections.namedtuple('IconSet', (
    'node_name',
    'role_names',
    'css_prefix',
    'icons'
))

# Each of the below classes describes an icon font. Each must provide:
# * A name for the docutils icon node
# * A name for the docutils role
# * A prefix for the CSS class attached to the output <span>
# * A set  of known icon names
# Request new icons from the PPO team

#: FontAwesome 5 Solid icon font
ICONS_FA5 = IconSet(
    node_name='IconFA5',
    role_names=('icon-fa5', 'icon'),
    css_prefix='fas fa-',
    icons=set((
        'caret-right',
        'caret-square-left',
        'caret-square-right',
        'check-circle',
        'check-square',
        'copy',
        'edit',
        'exclamation-circle',
        'eye',
        'globe',
        'lock',
        'pencil-alt',
        'save',
        'star',
        'sync-alt',
        'trash',
        'trash-alt',
        'users',

        # Discouraged, but not prohibited
        'arrow-right',
        'asterisk',
        'check',
        'ellipsis-h',
        'minus',
        'plus',
    )))

#: FontAwesome 5 Brand icon font
ICONS_BRANDS_FA5 = IconSet(
    node_name='IconBrandFA5',
    role_names=('icon-fa5-brands', 'iconb'),
    css_prefix='fab fa-',
    icons=set((
        'windows',
    )))

#: FontAwesome 4.7 icon font
ICONS_FA4 = IconSet(
    node_name='IconFA4',
    role_names=('icon-fa4',),
    css_prefix='fa4 fa4-',
    icons=set((
        'book',
        'caret-down',
        'caret-right',
        'circle',
        'download',
        'exclamation-circle',
        'exclamation-triangle',
        'globe',
        'info',
        'info-circle',
        'lock',
        'pencil',
        'plus',
        'plus-square',
        'question-circle',
        'refresh',
        'search',
        'stop',
        'times-circle',
        'trash-o'
    )))

#: MMS icon font
ICONS_MMS = IconSet(
    node_name='IconMMS',
    role_names=('icon-mms',),
    css_prefix='mms-icon mms-icon-',
    icons=set((
        '2fa',
        'activity',
        'add',
        'addcenter',
        'api',
        'auth',
        'back',
        'bell',
        'check',
        'cloud',
        'configsvr-startup2',
        'continuous',
        'creditcard',
        'dashboard',
        'database',
        'databases',
        'deadface',
        'dragleft',
        'dragtopleft',
        'edit',
        'ellipsis',
        'floppy',
        'graph',
        'grid',
        'hammer',
        'laptop',
        'list',
        'list-skinny',
        'lock',
        'logo-amazon',
        'logo-apple',
        'logo-linux',
        'logo-redhat',
        'logo-ubuntu',
        'logo-windows',
        'medium-cloud',
        'metrics',
        'modify',
        'office',
        'ops-manager',
        'paused',
        'pointintime',
        'remove',
        'replica-set-configsvr',
        'rocketbot',
        'sadface',
        'servers',
        'settings',
        'setup',
        'smartphone',
        'ssl',
        'startup2',
        'support1',
        'support2',
        'surprisedface',
        'topology',
        'umbrella'
    ) + tuple('wrench' + mode for mode in ('',) + ALL_SUFFIXES)))

# Add MMS icon permutations
for mode in ('', '-add', '-edit', '-remove', '-restart'):
    # Agents
    ICONS_MMS.icons.update(icon + mode for icon in (
        'monitoring',
        'backup',
        'automation'
    ))

    # Deployment Items
    ICONS_MMS.icons.update(icon + mode for icon in (
        'standalone',
        'replica-set',
        'cluster',
        'mongos'
    ))

    # Replica Set Members
    ICONS_MMS.icons.update(icon + mode for icon in (
        'primary',
        'secondary',
        'arbiter',
        'hidden-s',
        'delayed',
        'nostate',
        'startup',
        'recovering',
        'rollback',
        'down',
        'fatal',
        'shunned',
        'unknown'
    ))

    # Config Server Replica Sets
    ICONS_MMS.icons.update(icon + mode for icon in (
        'configsvr',
        'configsvr-arbiter',
        'configsvr-delayed',
        'configsvr-down',
        'configsvr-fatal',
        'configsvr-hidden',
        'configsvr-nostate',
        'configsvr-primary',
        'configsvr-recovering',
        'configsvr-rollback',
        'configsvr-secondary',
        'configsvr-shunned',
        'configsvr-startup',
        'configsvr-unknown'
    ))

    # Other Managed Features
    ICONS_MMS.icons.update(icon + mode for icon in (
        'group',
        'user',
        'role',
        'leaf',
        'server'
    ))

#: MMS Org icon font
ICONS_MMS_ORG = IconSet(
    node_name='IconMMSOrg',
    role_names=('icon-mms-org',),
    css_prefix='mms-org-icon mms-org-icon-',
    icons=set((
        'activity-feed',
    )))

#: Charts icons
ICONS_CHARTS = IconSet(
    node_name='IconCharts',
    role_names=('icon-charts',),
    css_prefix='charts-icon charts-icon-',
    icons=set((
        'geoglobe',
    )))


def class_to_label(css_class):
    """Approximate a label for screen readers from a CSS class name."""
    return PAT_STRIP.sub('', css_class).replace('-', ' ') + ' icon'


def create_icon_set(app, icon_set):
    """Create an icon role in the given Sphinx app using the information
       in the provided class."""
    class IconNode(nodes.General, nodes.Inline, nodes.Element):
        """Docutils node for representing an icon."""
        @staticmethod
        def visit_icon(self, node):
            icon_name = node['icon_name']
            mms_emblem = node['mms_emblem']
            have_emblem_class = ' {}-{} mms-have-emblem'.format(
                icon_set.css_prefix + icon_name,
                mms_emblem) if mms_emblem else ''

            # I've tested the screenreader behavior in Safari w/ macOS Voiceover
            self.body.append(
                self.starttag(
                    node,
                    'span',
                    CLASS=icon_set.css_prefix + icon_name + have_emblem_class,
                    **{'title': node['label']}))
            if mms_emblem:
                self.body.append(
                    self.starttag(
                        node,
                        'span',
                        CLASS='mms-emblem mms-emblem-{}'.format(mms_emblem)))
                self.body.append('</span>')
            self.body.append(self.starttag(node, 'span', CLASS='screenreader'))
            self.body.append(node['label'])

        @staticmethod
        def depart_icon(self, node=None):
            self.body.append('</span></span>\n')

    # Rename the node we just created
    IconNode.__qualname__ = IconNode.__name__ = icon_set.node_name
    # Make the IconNode available as an attribute in this module so that
    # it is picklable because Sphinx pickles doctrees. For example,
    # IconNode might be accessible as 'icon.IconFA5'.
    globals()[icon_set.node_name] = IconNode

    class IconGenerateHelpDirective(Directive):
        """A directive that generates a list-table of all the possible
           icons in the given icon_set."""
        has_content = False
        required_arguments = 0
        optional_arguments = 0
        option_spec = {}

        def run(self):
            try:
                rendered = HELP_TEMPLATE.render({
                    'role': icon_set.role_names[0],
                    'icons': sorted(icon_set.icons)
                })
            except Exception as error:
                raise self.severe('Failed to render template: {}'.format(ErrorString(error)))

            rendered_lines = statemachine.string2lines(rendered, 4, convert_whitespace=1)
            self.state_machine.insert_input(rendered_lines, '')
            return []

    def icon_role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
        """Docutils role which instantiates an IconNode."""
        errors = []
        has_explicit_title, label, icon_name = split_explicit_title(text)
        if icon_name not in icon_set.icons:
            msg = 'Unknown {} icon: {}'.format(typ, icon_name)
            errors.append(inliner.reporter.error(msg, line=lineno))

        label = label if has_explicit_title else class_to_label(icon_name)
        config = inliner.document.settings.env.config

        # Some MMS icon fonts contain an emblem; e.g. an "add" or "edit" emblem in one corner.
        # Try to find such a suffix, and split it off.
        emblem = next((suffix for suffix in ALL_SUFFIXES if icon_name.endswith(suffix)), '')
        if emblem:
            icon_name = icon_name[:len(icon_name) - len(emblem)]
            emblem = emblem.lstrip('-')

        if config._raw_config['tags'].eval_condition('html'):
            return [IconNode(icon_name=icon_name, label=label, mms_emblem=emblem)], []

        return [nodes.Text(label)], errors

    app.add_node(IconNode, html=(IconNode.visit_icon, IconNode.depart_icon))
    app.add_directive('{}-help'.format(icon_set.role_names[0]), IconGenerateHelpDirective)
    for role_name in icon_set.role_names:
        roles.register_local_role(role_name, icon_role)


def setup(app):
    # For MMS
    create_icon_set(app, ICONS_MMS_ORG)
    create_icon_set(app, ICONS_MMS)
    create_icon_set(app, ICONS_FA4)

    # For Charts
    create_icon_set(app, ICONS_CHARTS)

    # For everything else, there's MasterCard. Also FontAwesome 5.
    create_icon_set(app, ICONS_FA5)
    create_icon_set(app, ICONS_BRANDS_FA5)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
