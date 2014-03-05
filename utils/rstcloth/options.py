import os
import sys

from jinja2 import Template

from utils.rstcloth.rstcloth import RstCloth
from utils.structures import AttributeDict
from utils.serialization import ingest_yaml_list
from utils.files import expand_tree

class Options(object):
    def __init__(self, fn=None):
        self.data = list()
        self.cache = dict()
        self.source_files = list()
        self.unresolved = list()
        if fn is not None:
            self.source_dirname = os.path.dirname(os.path.abspath(fn))
        else:
            self.source_dirname = fn

        if fn is not None:
            self.ingest(fn)

    def ingest(self, fn):
        if self.source_dirname is None:
            self.source_dirname = os.path.dirname(os.path.abspath(fn))

        self.source_files.append(fn)
        input_sources = ingest_yaml_list(os.path.join(self.source_dirname, os.path.basename(fn)))
        self.cache[fn] = dict()

        for option in input_sources:
            opt = Option(option)

            self.cache_option(opt, fn)

        self.resolve(fn)

    def cache_option(self, opt, fn):
        if opt.program not in self.cache[fn]:
            self.cache[fn][opt.program] = dict()

        self.cache[fn][opt.program][opt.name] = opt

        if opt.inherited is True:
            self.unresolved.append(opt)
        else:
            self.data.append(opt)

    def resolve(self, fn):
        for opt in self.unresolved:
            if opt.inherited is True:
                if opt.source.file == fn:
                    continue

                if opt.source.file in self.cache:
                    base_opt = self.resolve_inherited(opt.source)
                else:
                    self.ingest(opt.source.file)
                    base_opt = self.resolve_inherited(opt.source)

                base_opt.doc.update(opt.doc)
                if 'inherit' in base_opt.doc:
                    del base_opt.doc['inherit']

                opt = Option(base_opt.doc)
                self.cache_option(opt, fn)

        self.unresolved = list()

    def resolve_inherited(self, spec):
        return self.cache[spec.file][spec.program][spec.name]

    def iterator(self):
        for item in self.data:
            if not item.program.startswith('_'):
                yield item

optional_source_fields = ['default', 'type', 'pre', 'description', 'post', 'directive']

class Option(object):
    def __init__(self, doc):
        self.doc = doc

        self.name = doc['name']
        self.program = doc['program']

        self._directive = 'describe'

        for k in optional_source_fields:
            if k in doc:
                setattr(self, k, doc[k])
            else:
                setattr(self, k, None)

        if 'inherit' in doc:
            self.inherited = True
            self.source = AttributeDict(doc['inherit'])
        else:
            self.inherited = False
            self.source = AttributeDict()

        if 'args' in doc:
            if doc['args'] is None or doc['args'] == '':
                pass
            else:
                self.arguments = doc['args']

        if 'aliases' in doc:
            if doc['aliases'] is None or doc['aliases'] == '':
                pass
            else:
                if isinstance(doc['aliases'], list):
                    self.aliases = doc['aliases']
                else:
                    self.aliases = [ doc['aliases'] ]

        self.replacement = dict()
        if 'replacement' in doc:
            if isinstance(doc['replacement'], dict):
                self.replacement = doc['replacement']

        # add auto-populated replacements here
        self.add_replacements()

    @property
    def directive(self):
        return self._directive

    @directive.setter
    def directive(self, value):
        self._directive = value

    def add_replacements(self):
        if not self.program.startswith('_'):
            if 'program' not in self.replacement:
                self.replacement['program'] = ':program:`{0}`'.format(self.program)
            if 'role' not in self.replacement:
                if self.directive == 'describe': 
                    self.replacement['role'] = "``{0}``".format(self.name)
                elif self.directive == 'option': 
                    self.replacement['role'] = ":{0}:`--{1}`".format(self.directive, self.name)
                else:
                    self.replacement['role'] = ":{0}:`{1}`".format(self.directive, self.name)

    def replace(self):
        for i in range(10):
            template = Template(self.description)
            self.description = template.render(**self.replacement)

            if "{{" not in self.description:
                break


class OptionRendered(object):
    def __init__(self, option):
        if not isinstance(option, Option):
            raise TypeError
        else:
            self.option = option

        self.rst = RstCloth()

    def resolve_option_name(self):
        if self.option.directive == 'option':
            if self.option.name.startswith('<'):
                prefix = ''
            else:
                prefix = '--'


            if hasattr(self.option, 'aliases'):
                if hasattr(self.option, 'arguments'):
                    return '{0}{1} {2}, {3}'.format(prefix, self.option.name,
                                                    self.option.arguments,
                                                    '{0}, '.format(self.option.arguments).join(self.option.aliases))
                else:
                    return '{0}{1}, {2}'.format(prefix, self.option.name,
                                                ', '.join(self.option.aliases))

            else:
                if hasattr(self.option, 'arguments'):
                    return '{0}{1} {2}'.format(prefix, self.option.name,
                                               self.option.arguments)
                else:
                    return '{0}{1}'.format(prefix, self.option.name)
        else:
            return self.option.name

    def resolve_output_path(self, path):
        name_parts = self.option.name.split(',')

        if len(name_parts) > 1:
            clensed_name = name_parts[0]
        else:
            clensed_name = self.option.name

        fn = '-'.join([ self.option.directive, self.option.program, clensed_name ]) + '.rst'
        return os.path.join(path, fn)

    def render(self, path):
        self.option.replace()

        self.rst.directive(self.option.directive, self.resolve_option_name())
        self.rst.newline()

        if self.option.default is not None:
            self.rst.content('*Default*: {0}'.format(self.option.default), indent=3)
            self.rst.newline()

        if self.option.type is not None:
            self.rst.content('*Type*: {0}'.format(self.option.type), indent=3)
            self.rst.newline()

        if self.option.pre is not None:
            self.rst.content(self.option.pre.split('\n'), indent=3, wrap=False)
            self.rst.newline()

        if self.option.description is not None:
            self.rst.content(self.option.description.split('\n'), indent=3, wrap=False)
            self.rst.newline()

        if self.option.post is not None:
            self.rst.content(self.option.post.split('\n'), indent=3, wrap=False)
            self.rst.newline()

        output_file = self.resolve_output_path(path)
        self.rst.write(output_file)

def main(files):
    options = Options()

    for fn in expand_tree('./','yaml'):
        options.ingest(fn)

    for opt in options.iterator():
        renderer = OptionRendered(opt)
        renderer.render(os.path.dirname(fn))

if __name__ == '__main__':
    main(sys.argv[1])
