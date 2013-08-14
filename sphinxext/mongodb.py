# -*- coding: utf-8 -*-
"""
    MongoDB Domain for Sphinx
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Based on the default JavaScript domain distributed with Sphinx.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.

    Additional work to adapt for MongoDB purposes done by 10gen,
    inc. (Sam Kleinman, et al.)
"""

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.domains.python import _pseudo_parse_arglist
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import Field, GroupedField, TypedField

from mongodb_conf import conf

def basename(path):
    return path.split('/')[-1].rsplit('.', 1)[0]

class MongoDBObject(ObjectDescription):
    """
    Description of a MongoDB object.
    """
    #: If set to ``True`` this object is callable and a `desc_parameterlist` is
    #: added
    has_arguments = False

    #: what is displayed right before the documentation entry
    display_prefix = None

    def handle_signature(self, sig, signode):
        sig = sig.strip()
        if '(' in sig and sig[-1:] == ')':
            prefix, arglist = sig.split('(', 1)
            prefix = prefix.strip()
            arglist = arglist[:-1].strip()
        else:
            prefix = sig
            arglist = None
        if '.' in prefix:
            nameprefix, name = prefix.rsplit('.', 1)
        else:
            nameprefix = None
            name = prefix

        objectname = self.env.temp_data.get('mongodb:object')
        if nameprefix:
            if objectname:
                # someone documenting the method of an attribute of the current
                # object? shouldn't happen but who knows...
                nameprefix = objectname + '.' + nameprefix
            fullname = nameprefix + '.' + name
        elif objectname:
            fullname = objectname + '.' + name
        else:
            # just a function or constructor
            objectname = ''
            fullname = name

        signode['object'] = objectname
        signode['fullname'] = fullname

        if self.display_prefix:
            signode += addnodes.desc_annotation(self.display_prefix,
                                                self.display_prefix)

        if nameprefix:
            if nameprefix in conf['suppress-prefix']:
                pass
            else:
                nameprefix += '.'
                for prefix in conf['suppress-prefix']:
                    if nameprefix.startswith(prefix):
                        nameprefix = nameprefix[len(prefix)+1:]
                        break

                signode += addnodes.desc_addname(nameprefix, nameprefix)
                nameprefix[:-1]

        signode += addnodes.desc_name(name, name)
        if self.has_arguments:
            if not arglist:
                signode += addnodes.desc_parameterlist()
            else:
                _pseudo_parse_arglist(signode, arglist)
        return fullname, nameprefix

    def add_target_and_index(self, name_obj, sig, signode):
        objectname = self.options.get(
            'object', self.env.temp_data.get('mongodb:object'))

        if self.objtype != 'program' and self.objtype in conf['prepend'].keys():
            fullname = '.'.join([conf['prepend'][self.objtype], name_obj[0]])
        elif name_obj[0] in self.state.document.ids:
            fullname = 'iddup.' + name_obj[0]
        else:
            fullname = name_obj[0]

        signode['names'].append(fullname)
        signode['ids'].append(fullname.replace('$', '_S_'))
        signode['first'] = not self.names
        self.state.document.note_explicit_target(signode)

        objects = self.env.domaindata['mongodb']['objects']
        if fullname in objects:
            path = self.env.doc2path(self.env.domaindata['mongodb']['objects'][fullname][0])
            spath = basename(path)
            sspath = basename(self.state_machine.reporter.source)

            if spath in conf['composites']:
                pass
            elif sspath in conf['composites']:
                pass
            elif spath == fullname:
                pass
            elif spath == fullname.lstrip('$'):
                pass
            elif spath == fullname.lstrip('_'):
                pass
            elif path == self.state_machine.reporter.source:
                pass
            elif fullname.startswith(spath):
                pass
            elif fullname == '$':
                pass
                # temporary: silencing the positional operator
                # warning, this is the namespace clash for
                # projection and query/update operators.
            else:
                self.state_machine.reporter.warning(
                    'duplicate object description of "%s", ' % fullname +
                    'other instance in ' + path,
                    line=self.lineno)

        if self.env.docname.rsplit('/', 1)[1] in conf['composites']:
            pass
        else:
            objects[fullname] = self.env.docname, self.objtype


        indextext = self.get_index_text(objectname, name_obj)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname.replace('$', '_S_'),
                                              ''))

    def get_index_text(self, objectname, name_obj):
        name, obj = name_obj

        for directive in conf['directives']:
            if self.objtype == directive['name']:
                return _('%s (' + directive['description'] + ')') % name

        return ''

    def run(self):
        return super(MongoDBObject, self).run()

    doc_field_types = [
        TypedField('arguments', label=l_('Arguments'),
                   names=('argument', 'arg'),
                   typerolename='method', typenames=('paramtype', 'type')),
        TypedField('options', label=l_('Options'),
                   names=('options', 'opts', 'option', 'opt'),
                   typerolename=('dbcommand', 'setting', 'status', 'stats', 'aggregator', 'data'),
                   typenames=('optstype', 'type')),
        TypedField('parameters', label=l_('Parameters'),
                   names=('param', 'paramter', 'parameters'),
                   typerolename=('dbcommand', 'setting', 'status', 'stats', 'aggregator', 'data'),
                   typenames=('paramtype', 'type')),
        TypedField('fields', label=l_('Fields'),
                   names=('fields', 'fields', 'field', 'field'),
                   typerolename=('dbcommand', 'setting', 'status', 'stats', 'aggregator', 'data'),
                   typenames=('fieldtype', 'type')),
        TypedField('flags', label=l_('Flags'),
                   names=('flags', 'flags', 'flag', 'flag'),
                   typerolename=('dbcommand', 'setting', 'status', 'stats', 'aggregator', 'data'),
                   typenames=('flagtype', 'type')),
        GroupedField('errors', label=l_('Throws'), rolename='err',
                     names=('throws', ),
                     can_collapse=True),
        GroupedField('exception', label=l_('Exception'), rolename='err',
                     names=('exception', ),
                     can_collapse=True),
        Field('returnvalue', label=l_('Returns'), has_arg=False,
              names=('returns', 'return')),
        Field('returntype', label=l_('Return type'), has_arg=False,
              names=('rtype',)),
    ]

class MongoDBMethod(MongoDBObject):
    has_arguments = True

class MongoDBXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        # basically what sphinx.domains.python.PyXRefRole does
        refnode['mongodb:object'] = env.temp_data.get('mongodb:object')
        if not has_explicit_title:
            title = title.lstrip('.')
            target = target.lstrip('~')
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind('.')
                if dot != -1:
                    title = title[dot+1:]
        if target[0:1] == '.':
            target = target[1:]
            refnode['refspecific'] = True
        return title, target

def render_domain_data(mongodb_directives):
    directives = { }
    roles = { }
    object_types = { }

    for directive in mongodb_directives:
        reftype = directive['name']

        roles[reftype] = MongoDBXRefRole()
        object_types[reftype] = ObjType(l_(reftype), reftype)

        if directive['callable']:
            directives[reftype] = MongoDBMethod
        else:
            directives[reftype] = MongoDBObject

    return directives, roles, object_types

class MongoDBDomain(Domain):
    """MongoDB Documentation domain."""
    name = 'mongodb'
    label = 'MongoDB'
    # if you add a new object type make sure to edit MongoDBObject.get_index_string

    directives, roles, object_types = render_domain_data(conf['directives'])

    initial_data = {
        'objects': {}, # fullname -> docname, objtype
    }

    def find_obj(self, env, obj, name, typ, searchorder=0):
        if name[-2:] == '()':
            name = name[:-2]
        objects = self.data['objects']
        newname = None

        if typ != 'binary' and typ in conf['prepend'].keys():
            name = '.'.join([conf['prepend'][typ], name])
            newname = name

        searchorder = 1

        if searchorder == 1:
            if obj and obj + '.' + name in objects:
                newname = obj + '.' + name
            else:
                # almost everything hits this branch in ecosystem
                newname = name
        else:
            if name in objects:
                newname = name
            elif obj and obj + '.' + name in objects:
                newname = obj + '.' + name

        return newname, objects.get(newname)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        objectname = node.get('mongodb:object')
        searchorder = node.hasattr('refspecific') and 1 or 0

        name, obj = self.find_obj(env, objectname, target, typ, searchorder)

        if obj is not None:
            if fromdocname == obj[0]:
                return None

        if obj is None:
            name, obj = self.find_obj(env, 'iddup.' + name, target, typ, searchorder)

            if obj is None:
                # print names and info from the node object at this
                # point to report on links that fail to resolve
                return None

        return make_refnode(builder, fromdocname, obj[0],
                            name.replace('$', '_S_'), contnode, target)

    def get_objects(self):
        for refname, (docname, type) in self.data['objects'].items():
            yield refname, refname, type, docname, refname.replace('$', '_S_'), 1

def setup(app):
    app.add_domain(MongoDBDomain)
