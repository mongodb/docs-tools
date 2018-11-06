'''
NOTE: This is a direct replacement of the writers in fasthtml.py
      If you use this, make sure that you remove 'fasthtml' from the list of
      extensions in 'conf.py'.
'''

import logging
import sys
from sphinx.util.osutil import relative_uri
from sphinx.builders.html import StandaloneHTMLBuilder, DirectoryHTMLBuilder
from sphinx import addnodes
import json

logger = logging.getLogger("fasthtml")

TOC_EXCLUDED = [
    "genindex",
    "search"
]

def is_http(url):
    return url.startswith("http://") or url.startswith("https://")


class TocPage:
    def __init__(self, display_name, slug, parent_section=None):
        self.display_name = display_name
        self.slug = slug
        self.parent_section = parent_section
        self.children = []

    def __repr__(self):
        return u'<TocPage name="{}" parent="{}" slug="{}" />'.format(
            self.display_name, self.parent_section.caption, self.slug
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def get_lineage(self):
        lineage = self.parent_section.get_lineage()
        if isinstance(self.parent_section, TocPage):
            lineage.append({
                "text": self.parent_section.display_name,
                "slug": self.parent_section.slug,
                "link": self.parent_section.slug
            })
        return lineage

    @property
    def child_pages(self):
        return [child for child in self.children if isinstance(child, TocPage)]

    @property
    def child_sections(self):
        return [child for child in self.children if isinstance(child, TocSection)]

    @property
    def all_descendant_pages(self):
        pages = list(self.child_pages)
        for child in self.children:
            pages.extend(child.all_descendant_pages)
        return pages

    def get_all_descendant_slugs(self):
        """List all child, grand-child, etc. page slugs."""
        descendant_slugs = []
        for child in self.children:
            if isinstance(child, TocPage):
                descendant_slugs.append(child["slug"])
            descendant_slugs.extend(child.get_all_descendant_slugs())
        return descendant_slugs

    def as_dict(self):
        return {
            "display_name": self.display_name,
            "slug": self.slug,
            "parent_section_caption": self.parent_section.caption,
            "lineage": self.get_lineage(),
            "children": [child.as_dict() for child in self.children]
        }


class TocSection:
    def __init__(self, parent=None, caption=None, entries=[]):
        self.is_root = False  # bool: True if this doesn't have a parent section.
        self.parent = parent  # str: slug of the parent page
        self.parent_section = None  # TocSection: The TocSection that contains this one
        self.caption = caption  # str: The section label
        self.children = self.children_from_toctree_entries(
            entries
        )  # list<TocSection|TocPage>: The children of this section

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return "".join(
            [
                u'<TocSection caption="{}" parent="{}" lineage="{}">'.format(
                    self.caption, self.parent, self.get_lineage()
                ),
                u"".join([str(child) for child in self.children]),
                u"</TocSection>",
            ]
        )

    def as_dict(self):
        return {
            "parent_slug": self.parent,
            "caption": self.caption,
            "children": [child.as_dict() for child in self.children],
        }

    def get_lineage(self):
        parent = self.parent_section
        this_section = {
            "text": self.caption,
            "slug": self.parent
        }
        # TODO: Make links work for nested, non-root sections if appropriate
        if self.is_root:
            overview_page = self.child_pages[0]
            this_section["link"] = overview_page.slug
        lineage = []
        if parent:
            lineage.extend(parent.get_lineage())
        lineage.append(this_section)
        return lineage


    @property
    def siblings(self):
        return self.parent_section.children if self.parent_section else []

    @property
    def sibling_pages(self):
        return self.parent_section.child_pages if self.parent_section else []

    @property
    def sibling_sections(self):
        return self.parent_section.child_sections if self.parent_section else []

    @property
    def child_pages(self):
        return [child for child in self.children if isinstance(child, TocPage)]

    @property
    def child_sections(self):
        return [child for child in self.children if isinstance(child, TocSection)]

    @property
    def all_descendant_pages(self):
        pages = list(self.child_pages)
        for child in self.children:
            pages.extend(child.all_descendant_pages)
        return pages

    @staticmethod
    def create_from(toctree):
        """Create a new TocSection from a toctree node."""
        section = TocSection(
            parent=toctree["parent"],
            entries=toctree["entries"],
            caption=toctree["caption"],
        )
        return section

    def children_from_toctree_entries(self, entries):
        children = [TocPage(display_name, slug, parent_section=self) for display_name, slug in entries]
        return children

    def get_all_descendant_slugs(self):
        """List all child, grand-child, etc. page slugs."""
        descendant_slugs = []
        for child in self.children:
            if isinstance(child, TocPage):
                descendant_slugs.append(child["slug"])
            descendant_slugs.extend(child.get_all_descendant_slugs())
        return descendant_slugs

    def is_ancestor_of_slug(self, slug):
        return slug in self.get_all_descendant_slugs()

    def is_sibling_of_slug(self, slug):
        return slug in [page.slug for page in self.sibling_pages]

    def has_slug_as_child(self, slug):
        return slug in [page.slug for page in self.child_pages]

    def get_child_page(self, slug):
        try:
            page = [page for page in self.child_pages if page.slug == slug][0]
            return page
        except Exception as e:
            print('Something went wrong getting child page: {}'.format(slug))

    def add_nested_section(self, toc_section):
        # Track our success through the recursive stack
        successfully_added_section = False
        # Check if the section's parent is a direct child page
        if self.has_slug_as_child(toc_section.parent):
            if toc_section.caption:
                toc_section.parent_section = self
                self.children.append(toc_section)
                successfully_added_section = True
            else:
                page = self.get_child_page(toc_section.parent)
                toc_section.parent_section = page
                page.children.append(toc_section)
                successfully_added_section = True
        # Check if the section's parent is in a nested section's child pages
        else:
            for section in self.child_sections:
                successfully_added_section = section.add_nested_section(toc_section)
                if successfully_added_section:
                    break
        return successfully_added_section


class Toctree:
    def __init__(self, render_title, get_relative_uri):
        # Helper callbacks from the parent Builder
        self.render_title = render_title
        self.get_relative_uri = get_relative_uri

        self.initialized = False

        self.sections = []
        self.root = None

    def as_dict(self):
        return {
            "root_page": self.root,
            "sections": [section.as_dict() for section in self.sections]
        }

    def get_page(self, slug, app, env):
        page = None
        for section in self.sections:
            if page:
                break
            for descendant_page in section.all_descendant_pages:
                if slug == descendant_page.slug:
                    page = descendant_page
                    break
        if not page:
            meta = env.metadata.get(slug)
            is_orphan = meta and meta.get("orphan") is not None
            if not is_orphan and slug != self.root and slug not in TOC_EXCLUDED:
                app.warn("Cannot find a matching page for slug: {}".format(slug))
        return page

    def initialize(self, env, docname=None):
        """Build our owntoctree structure, since the way Sphinx structures its
           toctree is just plumb inconvenient and weird. If docname is None,
           start from the master document."""
        if self.initialized:
            return

        # Determine if we're at the root of the toctree
        root_stage = True if docname is None else False
        if root_stage:
            docname = env.config.master_doc
            self.root = docname

        # Get all toctree nodes
        doctree = env.get_doctree(docname)
        toctrees = [toctreenode for toctreenode in doctree.traverse(addnodes.toctree)]

        # Create a list that contains every toctree node as a non-nested
        # section object.
        toc_sections = [TocSection.create_from(toctree) for toctree in toctrees]
        for toc_section in toc_sections:
            if toc_section.parent == self.root:
                # This section is on the root page (a root section)
                toc_section.is_root = True
                self.sections.append(toc_section)
            else:
                # This section is nested inside of a root section
                for root_section in self.sections:
                    successfully_added_section = root_section.add_nested_section(
                        toc_section
                    )
                    if successfully_added_section:
                        break
                else:
                    raise Exception(u'Oops! {}\n\n{}'.format(toc_section.parent, toc_section))
                    # raise Exception(u'Oops! The "{}" section is not nested inside of a root section.\n\n{}'.format(toc_section, self.sections))
            for child_page in toc_section.child_pages:
                if not is_http(child_page.slug):
                    self.initialize(env, child_page.slug)

        if root_stage:
            self.initialized = True

    def render_page_html(self, section, page, cur_slug, level):
        """Convert a TocPage dict to an html string."""
        title = page["display_name"]
        slug = page["slug"]
        if title is None:
            title = self.render_title(slug)

        is_current = (
            " current" if page.slug == cur_slug else ""
        )  # replaces exact_current

        # TODO: Original fasthtml denotes if an <li> contains the
        # current page (i.e. a list, e.g. partner services) with the `current` variable
        # Update to use `contains_current`
        # contains_current =

        if is_http(slug):
            link = slug
            link_type = "external"
        else:
            link = self.get_relative_uri(cur_slug, slug)
            link_type = "internal"

        return u"""
            <li class="toctree-l{level}{contains_nested}">
                <a class="reference {link_type}{is_current}" href="{link}">{page_title}</a>
                {children}
            </li>
        """.format(
            level=level,
            link_type=link_type,
            is_current=is_current,
            link=link,
            page_title=title,
            contains_nested=' contains-nested' if page.children else "",
            children=self.render_page_children(page, cur_slug, level, level) if page.children else "",
        )

    def render_section_children(self, section, cur_slug, level, depth):
        children_html = ""
        for child in section.children:
            if isinstance(child, TocPage):
                children_html += self.render_page_html(
                    section, child, cur_slug, level + 1
                )
            elif isinstance(child, TocSection):
                children_html += self.render_section_html(
                    child, cur_slug, level, depth + 1
                )
        return children_html

    def render_page_children(self, page, cur_slug, level, depth):
        children_html = ""
        for child in page.children:
            if isinstance(child, TocPage):
                children_html += self.render_page_html(
                    section, child, cur_slug, level + 1
                )
            elif isinstance(child, TocSection):
                children_html += self.render_section_html(
                    child, cur_slug, level, depth + 1
                )
        return children_html

    def render_section_html(self, section, cur_slug, level, depth=None):
        # The section is "current" if it's supposed to be visible.
        is_current = (
            section.is_ancestor_of_slug(cur_slug)
            or section.is_sibling_of_slug(cur_slug)
            or any(
                [
                    sibling.is_ancestor_of_slug(cur_slug)
                    for sibling in section.sibling_sections
                ]
            )
        )

        is_root = True if not depth else False
        depth = depth if depth else level + 2

        # Create and hydrate faux-components
        section_level = level if is_root or not section.caption else level + 1
        contains_current_page = section.is_ancestor_of_slug(cur_slug)

        if section.caption:
            section_caption_template = u"""
                <h{depth} class="toc-section-heading{is_current}">
                    {caption}
                </h{depth}>
            """
            section_caption = section_caption_template.format(
                depth=depth,
                is_current=" current open" if (is_root and is_current) or not is_root else "",
                caption=section.caption,
            )

            section_template = u"""
                <li class="toctree-l{level}{is_current}{selected_item_root}">
                    {section_caption}
                    <ul class="toc-section{is_root}{is_current}">
                        {children}
                    </ul>
                </li>
            """
            section_html = section_template.format(
                level=section_level,
                is_root="-root" if is_root else "",
                is_current=" current" if (is_root and is_current) or not is_root else "",
                selected_item_root=" selected-item-root"
                if contains_current_page and is_root
                else "",
                section_caption=section_caption,
                children=self.render_section_children(
                    section, cur_slug, section_level, depth
                ),
            )
        else:
            is_current = (
                section.has_slug_as_child(cur_slug)
                or section.parent == cur_slug
            )

            subpage_template = u"""
                <ul class="toc-section-nested{is_current}">
                    {children}
                </ul>
            """
            section_html = subpage_template.format(
                is_current=" current" if is_current else "",
                children=self.render_section_children(
                    section, cur_slug, section_level, depth
                )
            )
        return section_html

    def html(self, cur_slug, level=1, slugs=None):
        if not self.root:
            raise ValueError("No roots in toctree")

        toc_sections_html = "\n".join(
            [
                self.render_section_html(section, cur_slug, level)
                for section in self.sections
            ]
        )
        toctree_html = u'<ul class="toctree-root">{}</ul>'.format(toc_sections_html)

        return [toctree_html]


class FastHTMLMixin:
    def _render_title(self, slug):
        return self.render_partial(self.env.titles[slug])["title"]


class FastHTMLBuilder(StandaloneHTMLBuilder, FastHTMLMixin):
    name = "html"
    allow_parallel = False

    def init(self):
        StandaloneHTMLBuilder.init(self)
        self.toctree = Toctree(self._render_title, self.get_relative_uri)

    def handle_page(
        self,
        docname,
        addctx,
        templatename="page.html",
        outfilename=None,
        event_arg=None,
    ):
        self.toctree.initialize(self.env)
        if docname == "index":
            with open('/Users/nick/sidebar/toctree.json', 'w') as file:
                json.dump(self.toctree.as_dict(), file)


        lineage = self._get_page_lineage(docname)
        processed_lineage = self._process_page_lineage(docname, lineage)
        addctx["lineage"] = processed_lineage

        StandaloneHTMLBuilder.handle_page(self, docname, addctx, templatename=templatename, outfilename=outfilename, event_arg=event_arg)

    def _get_page_lineage(self, docname, **kw):
        lineage = [{ "text": "Stitch", "link": self.toctree.root }]
        page = self.toctree.get_page(docname, self.app, self.env)
        if page:
            lineage.extend(page.get_lineage())
        return lineage

    def _process_page_lineage(self, docname, lineage):
        processed = []
        for ancestor in lineage:
            if not ancestor.get("text"):
                ancestor["text"] = self.toctree.render_title(ancestor["slug"])
            if ancestor.get("link"):
                ancestor["link"] = self.toctree.get_relative_uri(docname, ancestor["link"])
            processed.append(ancestor)
        return processed

    def _get_local_toctree(self, docname, collapse=True, **kwds):
        if "includehidden" not in kwds:
            kwds["includehidden"] = False

        toctree_html = "".join(self.toctree.html(docname))
        return toctree_html


class FastDirectoryHTMLBuilder(DirectoryHTMLBuilder, FastHTMLMixin):
    name = "dirhtml"

    def init(self):
        DirectoryHTMLBuilder.init(self)
        self.toctree = Toctree(self._render_title, self.get_relative_uri)

    def handle_page(
        self,
        pagename,
        addctx,
        templatename="page.html",
        outfilename=None,
        event_arg=None,
    ):
        self.toctree.initialize(self.env)
        # if pagename == "index":
        #     with open('/Users/nick/sidebar/toctree.json', 'w') as file:
        #         json.dump(self.toctree.as_dict(), file)

        DirectoryHTMLBuilder.handle_page(
            self,
            pagename,
            addctx,
            templatename=templatename,
            outfilename=outfilename,
            event_arg=event_arg,
        )

    def _get_local_toctree(self, docname, collapse=True, **kwds):
        if "includehidden" not in kwds:
            kwds["includehidden"] = False

        toctree_html = "".join(self.toctree.html(docname))
        return toctree_html


def setup(app):
    del app.registry.builders["html"]
    del app.registry.builders["dirhtml"]

    app.add_builder(FastHTMLBuilder)
    app.add_builder(FastDirectoryHTMLBuilder)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
