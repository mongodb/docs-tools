# Copyright 2020 MongoDB, inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from sphinx.util.osutil import relative_uri
from sphinx.builders.html import StandaloneHTMLBuilder, DirectoryHTMLBuilder
from sphinx import addnodes

logger = logging.getLogger('fasthtml')


class ListSet(list):
    def add(self, x):
        if not x in self:
            self.append(x)


def is_http(url):
    return url.startswith('http://') or url.startswith('https://')


class Toctree:
    def __init__(self, render_title, get_relative_uri):
        self.titles = {}  # type: Dict[str, str]
        self.parent = {}  # type: Dict[str, List[str]]
        self.children = {}   # type: Dict[str, List[str]]
        self.root = None

        # Helper callbacks from the parent Builder
        self.render_title = render_title
        self.get_relative_uri = get_relative_uri
        self.initialized = False

    def initialize(self, env, docname=None):
        """Build our owntoctree structure, since the way Sphinx structures its
           toctree is just plumb inconvenient and weird. If docname is None,
           start from the master document."""
        if self.initialized:
            return

        root_stage = False
        if docname is None:
            docname = env.config.master_doc
            self.root = docname
            root_stage = True

        doctree = env.get_doctree(docname)
        toctrees = []
        for toctreenode in doctree.traverse(addnodes.toctree):
            toctrees.append(toctreenode)

        if not toctrees:
            self.children[docname] = ListSet()
            return

        for toctree in toctrees:
            for title, child_docname in toctree['entries']:
                self.children.setdefault(docname, ListSet()).add((title, child_docname))
                self.parent.setdefault(child_docname, []).append(docname)
                if not is_http(child_docname):
                    self.initialize(env, child_docname)

        if root_stage:
            self.initialized = True

    def is_child_of(self, slug, ancestor):
        """Return True if slug is a child/grand-child/... of ancestor."""
        # Cheat to make the manual work
        if ancestor == self.root and slug == 'index':
            return True

        while True:
            if slug == ancestor:
                return True

            slugs = self.parent.get(slug, None)
            if slugs is None:
                return False

            if len(slugs) == 1:
                slug = slugs[0]
            else:
                for slug in slugs:
                    if self.is_child_of(slug, ancestor):
                        return True

                return False

    def html(self, cur_slug, level=1, slugs=None):
        if not self.root:
            raise ValueError('No roots in toctree')

        if slugs is None:
            slugs = self.children.get(self.root, ())

        tokens = []
        have_current = False
        tokens.append('<ul>')

        for title, slug in slugs:
            if title is None:
                title = self.get_title(slug)

            current = ' current' if self.is_child_of(cur_slug, slug) else ''
            if current:
                have_current = True
            exact_current = ' current' if cur_slug == slug else ''

            if is_http(slug):
                link = slug
                link_type = 'external'
            else:
                link = self.get_relative_uri(cur_slug, slug)
                link_type = 'internal'

            tokens.append(u'<li class="toctree-l{}{}"><a class="reference {}{}" href="{}">{}</a>'.format(level, current, link_type, exact_current, link, title))
            children = self.children.get(slug, ())

            if children:
                rendered_children = self.html(cur_slug, level+1, children)
                tokens.extend(rendered_children)

            tokens.append('</li>')

        tokens.append('</ul>')

        if have_current:
            tokens[0] = '<ul class="current">'

        return tokens

    def get_title(self, slug):
        if slug in self.titles:
            return self.titles[slug]

        title = self.render_title(slug)
        self.titles[slug] = title
        return title


class FastHTMLMixin:
    def _render_title(self, slug):
        return self.render_partial(self.env.titles[slug])['title']


class FastHTMLBuilder(StandaloneHTMLBuilder, FastHTMLMixin):
    name = 'html'

    def init(self):
        StandaloneHTMLBuilder.init(self)
        self.toctree = Toctree(self._render_title, self.get_relative_uri)

    def handle_page(self, pagename, addctx, templatename='page.html', outfilename=None, event_arg=None):
        self.toctree.initialize(self.env)
        StandaloneHTMLBuilder.handle_page(self, pagename, addctx, templatename=templatename, outfilename=outfilename, event_arg=event_arg)

    def _get_local_toctree(self, docname, collapse=True, **kwds):
        if 'includehidden' not in kwds:
            kwds['includehidden'] = False

        return ''.join(self.toctree.html(docname))


class FastDirectoryHTMLBuilder(DirectoryHTMLBuilder, FastHTMLMixin):
    name = 'dirhtml'

    def init(self):
        DirectoryHTMLBuilder.init(self)
        self.toctree = Toctree(self._render_title, self.get_relative_uri)

    def handle_page(self, pagename, addctx, templatename='page.html', outfilename=None, event_arg=None):
        self.toctree.initialize(self.env)
        DirectoryHTMLBuilder.handle_page(self, pagename, addctx, templatename=templatename, outfilename=outfilename, event_arg=event_arg)

    def _get_local_toctree(self, docname, collapse=True, **kwds):
        if 'includehidden' not in kwds:
            kwds['includehidden'] = False

        return ''.join(self.toctree.html(docname))


def setup(app):
    del app.registry.builders['html']
    del app.registry.builders['dirhtml']

    app.add_builder(FastHTMLBuilder)
    app.add_builder(FastDirectoryHTMLBuilder)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
