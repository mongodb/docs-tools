import os
import sys

try:
    from utils.rstcloth.rstcloth import RstCloth
    from utils.structures import AttributeDict
    from utils.serialization import ingest_yaml_list
    from utils.files import expand_tree
except ImportError:
    from ..rstcloth.rstcloth import RstCloth
    from ..structures import AttributeDict
    from ..serialization import ingest_yaml_list
    from ..files import expand_tree

class Options(object):
    def __init__(self, fn=None):
        self.data = list()
        self.cache = dict()
        self.source_files = list()
        self.unresolved = list()

        if fn is not None:
            self.ingest(fn)

    def ingest(self, fn):
        self.source_files.append(fn)
        input_sources = ingest_yaml_list(fn)
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
                if opt.source.file == fn or opt.source.file in self.cache:
                    raise Exception('[ERROR]: recursion error in {0}.'.format(fn))

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

        if 'inherit' in doc:
            self.inherited = True
            self.source = AttributeDict(doc['inherit'])
        else:
            self.inherited = False
            self.source = AttributeDict()

        if self.directive == 'option':
            if 'args' in doc:
                self.arguments = doc['args']
            else:
                self.arguments = ''

        self.replacement = dict()
        if 'replacement' in doc:
            self.replacement = doc['replacement']

        self.replacement['role'] = '{role}'
        if self.program != '_generic':
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
            if self.option.argumets.startswith(','):
                spacer = ''
            else:
                spacer = ' '

            return '--{0}{1}{2}'.format(self.option.name, spacer, self.option.arguments)
        else:
            return self.option.name

    def resolve_output_path(self, path):
        fn = '-'.join([ self.option.directive, self.option.name ]) + '.rst'
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

        self.rst.content(self.option.description, indent=3, wrap=False)

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
