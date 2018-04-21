from collections import OrderedDict
import json
import re
import fett
import yaml
from docutils.parsers.rst import Directive, directives
from docutils import statemachine, utils, nodes
from docutils.utils.error_reporting import ErrorString

# As of 2018-04, the OpenAPI Python libraries are immature and lack the
# features we need. This extension contains a quick-and-dirty hacky partial
# implementation of OpenAPI 3.0. It requires valid OpenAPI 3.0 input: it
# does no schema validation.


class DictLike:
    """Our templating engine accesses properties via indexing. This class
       mixin creates a __getitem__ wrapper around getattr."""
    def __getitem__(self, key):
        return getattr(self, key)


class TagDefinition(DictLike):
    """Resources are grouped by logical "tags"."""
    def __init__(self, name, title, operations):
        self.name = name
        self.title = title
        self.operations = operations


class FieldDescription(DictLike):
    """A field in a request body, response, or parameter."""
    def __init__(self, name, description, required, type, enum):
        # type: (str, str, bool, str) -> None
        self.name = name
        self.description = description
        self.required = required
        self.type = type
        self.enum = enum

    @classmethod
    def load(cls, data, name=None, required=None):
        # Merge the schema property, if there is one
        if 'schema' in data:
            for key, value in data['schema'].items():
                data[key] = value

        data_type = data.get('type', None)
        if data_type is None:
            if 'properties' in data:
                data_type = 'object'
            elif 'items' in data:
                data_type = 'array'

        if data_type is None:
            data_type = 'Any'

        return cls(
            name if name is not None else data['name'],
            data.get('description', ''),
            required if required is not None else data.get('required', False),
            data_type,
            data.get('enum', []))


HTTP_VERBS = ('post', 'get', 'put', 'patch', 'delete', 'options',
              'connect', 'trace', 'head')

# We notate HTTP path parameters with curly braces: e.g. /{foo}/bar
# Give these components a special span
PARAMATER_PATTERN = re.compile(r'\{\w+\}')
fett.Template.FILTERS['tagPathParameters'] = lambda val: PARAMATER_PATTERN.sub(
    lambda match: '<span class="apiref-resource__path-parameter">{}</span>'.format(match.group(0)),
    val)

fett.Template.FILTERS['values'] = lambda val: val.values()

PARAMETER_TEMPLATE = fett.Template('''
.. raw:: html

   <h3>{{ title }}</h3>

.. list-table::
   :header-rows: 1
   :widths: 25 10 65

   * - Name
     - Type
     - Description

{{ for parameter in parameters }}
   * - ``{{ parameter.name }}``
       {{ if parameter.required }}:raw-html:`<span class="apiref-resource__parameter-required-flag"></span>`
       {{ else }}:raw-html:`<span class="apiref-resource__parameter-optional-flag"></span>`{{ end }}
     - {{ parameter.type }}
     - {{ parameter.description }}{{ if parameter.enum }}

       Possible Values:

       {{ for val in parameter.enum }}
       - ``{{ val }}``

       {{ end }}
       {{ end }}

{{ end }}

''')

OPENAPI_TEMPLATE = fett.Template('''
.. role:: raw-html(raw)
   :format: html

{{ if servers }}
.. list-table::
   :header-rows: 1

   * - API Base URL
     - Description

{{ for server in servers }}
   * - {{ server.url }}
     - {{ server.description }}

{{ end }}
{{ end }}

{{ for tag in tags }}
{{ tag.title }}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{{ for operation in tag.operations }}

.. raw:: html

   <div class="apiref-resource apiref-resource--collapsed" id="{{ operation.hash }}">
     <div class="apiref-resource__header" role="button">
       <div class="apiref-resource__method apiref-resource__method--{{ operation.method escape }}">{{ operation.method escape }}</div>
       <div class="apiref-resource__path">{{ operation.path escape tagPathParameters }}</div>
     </div>
     <div class="apiref-resource__summary">

{{ operation.summary }}

.. raw:: html

     </div>
     <div class="apiref-resource__body">

{{ operation.path_parameters }}
{{ operation.query_parameters }}
{{ operation.header_parameters }}
{{ operation.cookie_parameters }}

{{ if operation.requestBody }}

.. raw:: html

   <h3>Request Body{{ if operation.requestBody.required }}
   <span class="apiref-resource__parameter-required-flag"></span>
   {{ else }}
   <span class="apiref-resource__parameter-optional-flag"></span>
   {{ end }}
   </h3>

{{ operation.requestBody.description }}

.. code-block:: json

   {{ operation.requestBody.jsonSchema }}

.. list-table::
   :header-rows: 1
   :widths: 40 10 50

   * - Field
     - Type
     - Description

{{ for field in operation.requestBody.jsonFields }}
   * - ``{{ field.name }}`` {{ if field.required }}:raw-html:`<span class="apiref-resource__parameter-required-flag"></span>`{{ else }}:raw-html:`<span class="apiref-resource__parameter-optional-flag"></span>`{{ end }}
     - {{ field.type }}
     - {{ field.description }}{{ if field.enum }}

       Possible Values:

       {{ for val in field.enum }}
       - ``{{ val }}``

       {{ end }}
       {{ end }}

{{ end }}

{{ end }}

.. raw:: html

   <h3>Responses</h3>

{{ for response in operation.responses values }}
``{{ response.code }}``: {{ response.description }}

{{ if response.jsonSchema }}
.. code-block:: json

   {{ response.jsonSchema }}

.. list-table::
   :header-rows: 1
   :widths: 40 10 50

   * - Field
     - Type
     - Description

{{ for field in response.jsonFields }}
   * - ``{{ field.name }}``
     - {{ field.type }}
     - {{ field.description }}{{ if field.enum }}

       Possible Values:

       {{ for val in field.enum }}
       - ``{{ val }}``

       {{ end }}
       {{ end }}

{{ end }}
{{ end }}
{{ end }}

.. raw:: html

   </div>
   </div>

{{ end }}

{{ end }}
''')


def ordered_load_yaml(stream):
    """Load a YAML stream, maintaining order of maps."""
    class OrderedLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)


# JavaScript Object Notation (JSON) Pointer
# See https://tools.ietf.org/html/rfc6901
def encode_json_pointer(ptr):
    return ptr.replace('~', '~0').replace('/', '~1')


def decode_json_pointer(ptr):
    return ptr.replace('~1', '/').replace('~0', '~')


def dereference_json_pointer(root, ptr):
    """Given a dictionary or list, return the element referred to by the
       given JSON pointer (RFC-6901)."""
    cursor = root
    components = ptr.lstrip('#').lstrip('/').split('/')
    for i, component in enumerate(components):
        component = decode_json_pointer(component)
        if isinstance(cursor, list):
            if component == '-':
                # "-" specifies the imaginary element *after* the last element of an array.
                # We don't need to support this, so... we don't.
                raise NotImplementedError('"-" list components not supported')

            component = int(component)
        elif not isinstance(cursor, dict):
            raise ValueError('Invalid entry type')

        cursor = cursor[component]

    return cursor


def schema_as_json(content_schema):
    """Create a JSON document describing the shape of an OpenAPI schema."""
    if 'properties' in content_schema:
        current = OrderedDict()
        for prop, options in content_schema['properties'].items():
            if 'type' not in options:
                current[prop] = 'Any'
            elif options['type'] == 'object':
                current[prop] = schema_as_json(options)
            elif options['type'] == 'array':
                current[prop] = [schema_as_json(options['items'])]
            else:
                current[prop] = options['type']

        return current

    if 'items' in content_schema:
        return [schema_as_json(content_schema['items'])]

    return content_schema['type']


def schema_as_fieldlist(content_schema, path=''):
    """Return a list of OpenAPI schema property descriptions."""
    fields = []

    if 'properties' in content_schema:
        required_fields = content_schema.get('required', ())

        for prop, options in content_schema['properties'].items():
            new_path = path + '.' + prop if path else prop
            required = options['required'] if 'required' in options else prop in required_fields

            if 'type' not in options:
                fields.append(FieldDescription.load(options, new_path, required))
            elif options['type'] == 'object':
                fields.append(FieldDescription.load(options, new_path, required))
                fields.extend(schema_as_fieldlist(options, path=new_path))
            elif options['type'] == 'array':
                fields.append(FieldDescription.load(options, new_path, required))
                fields.extend(schema_as_fieldlist(options['items'], path=new_path + '.[]'))
            else:
                fields.append(FieldDescription.load(options, new_path, required))

    if 'items' in content_schema:
        new_path = path + '.' + '[]' if path else '[]'
        options = content_schema['items']
        fields.append(FieldDescription.load(options, new_path))
        fields.extend(schema_as_fieldlist(options, path=new_path))

    return fields


def process_parameters(endpoint, operation):
    """Integrate an operation's parameters with the endpoint's shared
       set of parameters, and return a dictionary with two keys:
       * path_parameters
       * query_parameters
       * header_parameters
       * cookie_parameters"""
    all_parameters = endpoint.get('parameters', []) + operation.get('parameters', [])
    path_parameters = []
    query_parameters = []
    header_parameters = []
    cookie_parameters = []

    parameter_types = {
        'path': ('path_parameters', 'Path Parameters', path_parameters),
        'query': ('query_parameters', 'Query Parameters', query_parameters),
        'header': ('header_parameters', 'HTTP Header Parameters', header_parameters),
        'cookie': ('cookie_parameters', 'HTTP Cookie Parameters', cookie_parameters),
    }

    for parameter in all_parameters:
        parameter_types[parameter['in']][2].append(FieldDescription.load(parameter))

    result = {}
    for name, title, parameters in parameter_types.values():
        result[name] = PARAMETER_TEMPLATE.render({
            'title': title,
            'parameters': parameters
        }) if parameters else ''

    return result


class OpenAPI:
    __slots__ = ('data', 'tags')

    def __init__(self, data):
        self.data = data
        self.tags = OrderedDict()  # type: OrderedDict[str, TagDefinition]

        for tag_definition in self.data['tags']:
            self.tags[tag_definition['name']] = TagDefinition(
                tag_definition['name'],
                tag_definition.get('description', ''),
                [])

        # Substitute refs
        stack = [({}, '<root>', self.data)]
        while stack:
            parent, key, cursor = stack.pop()
            if isinstance(cursor, dict):
                cursor = self.dereference(cursor)
                parent[key] = cursor

                stack.extend((cursor, subkey, x) for subkey, x in cursor.items())
            elif isinstance(cursor, list):
                stack.extend((cursor, i, x) for i, x in enumerate(cursor))

        # Set up our operations
        for method, path, methods in self.resources():
            resource = methods[method]

            for tag in resource.get('tags', ()):
                if tag not in self.tags:
                    self.tags[tag] = TagDefinition(tag, '', [])

                resource.update({
                    'method': method,
                    'path': path,
                    'hash': '{}-{}'.format(method, path)
                })

                resource.setdefault('summary', '')
                resource.setdefault('requestBody', None)

                for code, response in resource['responses'].items():
                    response.update({
                        'code': code,
                        'jsonSchema': None,
                        'jsonFields': []
                    })

                    if 'content' in response and 'application/json' in response['content']:
                        json_schema = response['content']['application/json']['schema']
                        response['jsonSchema'] = json.dumps(schema_as_json(json_schema), indent=2)
                        response['jsonFields'] = schema_as_fieldlist(json_schema)

                if resource['requestBody'] is not None and 'application/json' in resource['requestBody']['content']:
                    resource['requestBody'].setdefault('required', False)
                    resource['requestBody'].setdefault('description', '')
                    json_schema = resource['requestBody']['content']['application/json']['schema']
                    resource['requestBody']['jsonSchema'] = json.dumps(schema_as_json(json_schema), indent=2)
                    resource['requestBody']['jsonFields'] = schema_as_fieldlist(json_schema)

                resource.update(process_parameters(methods, resource))

                self.tags[tag].operations.append(resource)

    def dereference(self, val, loop_set=None):
        """Dereference a $ref JSON pointer."""
        if not isinstance(val, dict):
            return val

        if len(val) == 1 and '$ref' in val:
            if loop_set is None:
                loop_set = set()

            if id(val) in loop_set:
                raise ValueError('$ref loop detected')

            val = dereference_json_pointer(self.data, val['$ref'])
            loop_set.add(id(val))
            return self.dereference(val, loop_set)

        return val

    def resources(self):
        """Enumerate resources listed within this OpenAPI tree."""
        for path, methods in self.data['paths'].items():
            for method in methods:
                if method.lower() not in HTTP_VERBS:
                    continue

                yield method, path, methods

    @classmethod
    def load(cls, data):
        """Load an OpenAPI file stream."""
        return cls(ordered_load_yaml(data))


class OpenAPIDirective(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env

        openapi_path = self.arguments[0]
        _, openapi_path = env.relfn2path(openapi_path)
        openapi_path = utils.relative_path(None, openapi_path)
        openapi_path = nodes.reprunicode(openapi_path)

        self.state.document.settings.record_dependencies.add(openapi_path)
        with open(openapi_path, 'r') as f:
            openapi = OpenAPI.load(f)

        try:
            rendered = OPENAPI_TEMPLATE.render({
                'tags': openapi.tags.values(),
                'servers': openapi.data['servers']
            })
        except Exception as error:
            raise self.severe('Failed to render template: {}'.format(ErrorString(error)))

        rendered_lines = statemachine.string2lines(rendered, 4, convert_whitespace=1)
        self.state_machine.insert_input(rendered_lines, '')

        # Allow people to use :ref: to link to resources. Sphinx offers two ways
        # of doing this: (1) lots of arcane boilerplate, or (2) hacking our way through.
        # Let's hope this doesn't break...
        stddomain = env.get_domain('std')
        labels = stddomain.data['labels']
        for method, path, methods in openapi.resources():
            method_hash = methods[method]['hash']
            if method_hash not in labels:
                labels[method_hash] = (env.docname, method_hash, '{} {}'.format(method.upper(), path))

        return []


def setup(app):
    directives.register_directive('openapi', OpenAPIDirective)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
