import warnings
import docutils
import docutils.utils
import sphinx.builders.text
import sphinx.writers.text
import sphinx.util.images

PAT_FILENAME_TEMPLATE = r'^{}(.+?)\.fjson$'


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

        self.pending_links.append(href)
        self.add_text('[')

    def depart_reference(self, node):
        self.add_text(']({})'.format(self.pending_links.pop()))

    def visit_literal_block(self, node):
        self.add_text('```')
        if 'language' in node and node['language'] != 'none':
            self.add_text(node['language'])

        self.new_state(0)

    def depart_literal_block(self, node):
        self.end_state(wrap=False)
        self.add_text('```')

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


def setup(app):
    app.add_builder(MarkdownBuilder)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
