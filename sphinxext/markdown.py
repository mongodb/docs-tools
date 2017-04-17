import codecs
import json
import logging
import os
import os.path
import re
import shutil
import sys
import sphinx.writers.text
import sphinx.builders.text
import docutils
from sphinx.util.osutil import SEP, os_path, relative_uri, ensuredir, movefile, copyfile
from sphinx.builders.html import StandaloneHTMLBuilder

logger = logging.getLogger('fasthtml')
PAT_FILENAME_TEMPLATE = r'^{}(.+?)\.fjson$'


class MarkdownTranslator(sphinx.writers.text.TextTranslator):
    def __init__(self, document, builder):
        sphinx.writers.text.TextTranslator.__init__(self, document, builder)
        self.nested_table = 0
        self.pending_links = []

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
            self.nested_table += 1
        else:
            sphinx.writers.text.TextTranslator.visit_table(self, node)

    def depart_table(self, node):
        if self.nested_table:
            self.nested_table -= 1
        else:
            sphinx.writers.text.TextTranslator.depart_table(self, node)

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
        if 'language' in node:
            self.add_text(node['language'])

        self.new_state(0)

    def depart_literal_block(self, node):
        self.end_state(wrap=False)
        self.add_text('```')


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
