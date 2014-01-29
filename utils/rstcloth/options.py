import os
import sys

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
                #
                # Commenting this out becuase it doesn't seem to be doing anything useful.'
                #
                # if opt.source.file == fn or opt.source.file in self.cache:
                #     raise Exception('[ERROR]: recursion error in {0}.'.format(fn))

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

class Option(object):
    def __init__(self, doc):
        self.doc = doc

        self.name = doc['name']

        self.program = doc['program']

        if 'default' in doc:
            self.default = doc['default']
        else:
            self.default = None

        if 'type' in doc:
            self.type = doc['type']
        else:
            self.type = None

        if 'directive' in doc:
            self.directive = doc['directive']
        else:
            self.directive = 'describe'

        if 'description' in doc:
            self.description = doc['description']
        else:
            self.description = ""

        if 'pre' in doc:
            self.pre = doc['pre']
        else:
            self.pre = None

        if 'post' in doc:
            self.post = doc['post']
        else:
            self.post = None

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
            if isnstance(doc['replacement'], dict):
                self.replacement = doc['replacement']

        self.replacement['role'] = '{role}'
        if not self.program.startswith('_'):
            self.replacement['program'] = ':program:`{0}`'.format(self.program)

    def replace(self):
        self.description = self.description.format(**self.replacement)

class OptionRendered(object):
    def __init__(self, option):
        if not isinstance(option, Option):
            raise TypeError
        else:
            self.option = option

        self.rst = RstCloth()

    def resolve_option_name(self):
        if self.option.directive == 'option':
            if hasattr(self.option, 'aliases'):
                if hasattr(self.option, 'arguments'):
                    return '--{0} {1}, {2}'.format(self.option.name,
                                                   self.option.arguments,
                                                   '{0}, '.format(self.option.arguments).join(self.option.aliases))
                else:
                    return '--{0}, {1}'.format(self.option.name,
                                              ', '.join(self.option.aliases))

            else:
                if hasattr(self.option, 'arguments'):
                    return '--{0} {1}'.format(self.option.name,
                                               self.option.arguments)
                else:
                    return '--{0}'.format(self.option.name)
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
            self.content('*Default*: {0}'.format(self.option.default))
            self.rst.newline()

        if self.option.type is not None:
            self.content('*Type*: {0}'.format(self.option.type))
            self.rst.newline()

        if self.option.pre is not None:
            self.rst.content(self.option.pre, indent=3, wrap=False)
            self.rst.newlin()

        self.rst.content(self.option.description, indent=3, wrap=False)

        if self.option.post is not None:
            self.rst.content(self.option.post, indent=3, wrap=False)
            self.rst.newlin()

        output_file = self.resolve_output_path(path)
        self.rst.write(output_file)

        print('[options]: rendered option file {0}'.format(output_file))


def main(files):
    options = Options()

    for fn in expand_tree('./','yaml'):
        options.ingest(fn)

    for opt in options.iterator():
        renderer = OptionRendered(opt)
        renderer.render(os.path.dirname(fn))

if __name__ == '__main__':
    main(sys.argv[1])
