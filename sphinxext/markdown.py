import os.path
import re
import warnings
import docutils
import docutils.utils
import sphinx.builders.text
import sphinx.util.images
import sphinx.writers.text
from sphinx.util.osutil import SEP

PAT_FILENAME_TEMPLATE = r'^{}(.+?)\.fjson$'
FILES = set(['2.6-downgrade', '2.6-upgrade-authorization', '2.6-upgrade', '3.0-downgrade', '3.0-scram', '3.0-upgrade', '3.2-downgrade', '3.2-upgrade', '3.4-downgrade-replica-set', '3.4-downgrade-sharded-cluster', '3.4-downgrade-standalone', '3.4-upgrade-replica-set', '3.4-upgrade-sharded-cluster', '3.4-upgrade-standalone', 'adjust-replica-set-member-priority', 'authenticate-nativeldap-activedirectory', 'backup-sharded-cluster-with-database-dumps', 'backup-sharded-cluster-with-filesystem-snapshots', 'backup-with-filesystem-snapshots', 'change-config-server-wiredtiger', 'change-own-password-and-custom-data', 'change-replica-set-wiredtiger', 'change-standalone-wiredtiger', 'clear-jumbo-flag', 'configure-fips', 'configure-ldap-sasl-activedirectory', 'configure-ldap-sasl-openldap', 'configure-secondary-only-replica-set-member', 'control-access-to-mongodb-windows-with-kerberos-authentication', 'control-access-to-mongodb-with-kerberos-authentication', 'convert-replica-set-to-replicated-shard-cluster', 'deploy-geographically-distributed-replica-set', 'deploy-replica-set-with-keyfile-access-control', 'deploy-replica-set', 'deploy-shard-cluster', 'deploy-sharded-cluster-hashed-sharding', 'deploy-sharded-cluster-ranged-sharding', 'deploy-sharded-cluster-with-keyfile-access-control', 'enable-authentication', 'enforce-keyfile-access-control-in-existing-replica-set-without-downtime', 'enforce-keyfile-access-control-in-existing-replica-set', 'enforce-keyfile-access-control-in-existing-sharded-cluster', 'install-mongodb-enterprise-on-amazon', 'install-mongodb-enterprise-on-debian', 'install-mongodb-enterprise-on-linux', 'install-mongodb-enterprise-on-os-x', 'install-mongodb-enterprise-on-red-hat', 'install-mongodb-enterprise-on-suse', 'install-mongodb-enterprise-on-ubuntu', 'install-mongodb-enterprise-on-windows', 'install-mongodb-on-amazon', 'install-mongodb-on-debian', 'install-mongodb-on-linux', 'install-mongodb-on-os-x', 'install-mongodb-on-red-hat', 'install-mongodb-on-suse', 'install-mongodb-on-ubuntu', 'install-mongodb-on-windows', 'kerberos-auth-activedirectory-authz', 'manage-sharded-cluster-balancer', 'manage-users-and-roles', 'migrate-sharded-cluster-to-new-hardware', 'monitor-with-snmp-on-windows', 'monitor-with-snmp', 'perform-findAndModify-linearizable-reads', 'perform-maintence-on-replica-set-members', 'perform-two-phase-commits', 'recover-data-following-unexpected-shutdown', 'replace-config-server', 'restore-replica-set-from-backup', 'restore-sharded-cluster', 'rotate-log-files', 'sharding-high-availability-writes', 'sharding-segmenting-data-by-location', 'sharding-segmenting-shards', 'sharding-tiered-hardware-for-varying-slas', 'text-search-with-rlp', 'transparent-huge-pages', 'verify-mongodb-packages'])


def warn(message, node):
    (source, line) = docutils.utils.get_source_line(node)
    if source and line:
        location = '{}:{}'.format(source, line)
    elif source:
        location = '{}:'.format(source)
    elif line:
        location = '<unknown>:{}'.format(line)

    warnings.warn('{}: {}'.format(location, message), Warning)


class MarkdownTranslator(sphinx.writers.text.TextTranslator):
    def __init__(self, document, builder):
        sphinx.writers.text.TextTranslator.__init__(self, document, builder)
        self.nested_table = 0
        self.pending_links = []
        self.pending_image = None
        self.source_path = None
        self.headmatter = None

        # The wrapping algorithm provided with the TextWriter breaks formatting.
        # Let's play it safe, and not bother wrapping.
        sphinx.writers.text.my_wrap = lambda s, *args, **kwargs: s.split('\n')

    def depart_title(self, node):
        text = ''.join(x[1] for x in self.states.pop() if x[0] == -1)
        self.stateindent.pop()
        title = ['', '#' * self.sectionlevel + ' ' + text, '']
        if len(self.states) == 2 and len(self.states[-1]) == 0:
            # remove an empty line before title if it is first section title in the document
            title.pop(0)
        self.states[-1].append((0, title))

    def visit_literal(self, node):
        self.add_text('``')

    def depart_literal(self, node):
        self.add_text('``')

    def visit_table(self, node):
        if self.table:
            warn('Nested table skipped', node)
            self.nested_table += 1
        else:
            sphinx.writers.text.TextTranslator.visit_table(self, node)

    def visit_reference(self, node):
        href = ''
        if 'refuri' in node:
            href = node['refuri'] or '#'
        else:
            assert 'refid' in node, \
                   'References must have "refuri" or "refid" attribute.'
            href = '#' + node['refid']

        docname = href.strip('/').split('/')[-1]
        if docname in FILES:
            href = '../' + docname + '/'
        elif not href.startswith('#') and not '://' in href:
            href = os.path.normpath(os.path.join(self.source_path, href))
            href = re.sub('^.*/source/', '', href)
            href = 'https://docs.mongodb.com/manual/{}'.format(href)

        self.pending_links.append(href)
        self.add_text('[')

    def depart_reference(self, node):
        self.add_text(']({})'.format(self.pending_links.pop()))

    def visit_literal_block(self, node):
        self.new_state(0)
        self.add_text('```')
        if 'language' in node and node['language'] != 'none':
            self.add_text(node['language'])

        self.new_state(0)

    def depart_literal_block(self, node):
        self.end_state(wrap=False)
        self.add_text('```')
        self.end_state(wrap=False)

    def visit_figure(self, node):
        assert not self.pending_image
        self.pending_image = (node.get('width', 0), node.get('height', 0))

    def depart_figure(self, node):
        self.pending_image = None

    def visit_image(self, node):
        parts = ['<img src="{}"'.format(node['uri'])]

        width = 0
        height = 0
        if self.pending_image:
            width, height = self.pending_image

        if 'width' in node:
            width = node['width']

        if 'height' in node:
            height = node['height']

        if 'scale' in node:
            warn('Image scaling unsupported', node)

        if 'align' in node:
            warn('Image alignment unsupported', node)

        if width:
            parts.append(' width="{}"'.format(width))

        if height:
            parts.append(' height="{}"'.format(height))

        if 'alt' in node:
            parts.append(' alt="{}"'.format(node['alt']))

        parts.append('>')

        self.add_text(''.join(parts))
        raise docutils.nodes.SkipNode

    def visit_topic(self, node):
        if 'contents' in node['classes']:
            raise docutils.nodes.SkipNode

        self.new_state(0)

    def visit_title(self, node):
        if not self.headmatter:
            self.headmatter = '''+++
title = "{}"

tags = [
"mongodb" ]
+++
'''.format(node.astext())

        sphinx.writers.text.TextTranslator.visit_title(self, node)

    def visit_document(self, node):
        self.source_path = node['source']
        sphinx.writers.text.TextTranslator.visit_document(self, node)

    def depart_document(self, node):
        sphinx.writers.text.TextTranslator.depart_document(self, node)
        self.body = self.headmatter + '\n' + self.body

    def depart_table(self, node):
        if self.nested_table:
            self.nested_table -= 1
            return

        lines = self.table[1:]
        n_cols = max(len(row) for row in lines)
        for row in lines:
            if row == 'sep':
                self.add_text('| - ' * n_cols + '|' + self.nl)
                continue

            out = ['|']
            for cell in row:
                out.append(' ' + cell.replace('\n', '') + ' |')

            self.add_text(''.join(out) + self.nl)

        self.table = None
        self.end_state(wrap=False)

    def visit_target(self, node):
        if 'refid' in node:
            self.add_text('<span id="{}"></span>'.format(node['refid'].replace('"', '\"')))
        sphinx.writers.text.TextTranslator.visit_target(self, node)


class MarkdownWriter(sphinx.writers.text.TextWriter):
    supported = ('markdown',)

    def __init__(self, builder):
        sphinx.writers.text.TextWriter.__init__(self, builder)
        self.translator_class = self.builder.translator_class or MarkdownTranslator


class MarkdownBuilder(sphinx.builders.text.TextBuilder):
    name = 'markdown'
    format = 'markdown'
    out_suffix = '.md'
    allow_parallel = True

    def prepare_writing(self, docnames):
        self.writer = MarkdownWriter(self)

    def get_target_uri(self, docname, typ=None):
        if docname == 'index':
            return ''

        if docname.endswith(SEP + 'index'):
            return docname[:-5]  # up to sep

        return docname + SEP


def setup(app):
    app.add_builder(MarkdownBuilder)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
