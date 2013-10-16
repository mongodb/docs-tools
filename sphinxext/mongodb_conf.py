import yaml

try:
    with open('mongodb-domain.yaml', 'r') as f:
        conf = yaml.safe_load_all(f).next()
except IOError:
    conf = { 'composites': [], 'suppress-prefix': [] }

conf['directives'] = [
    {
        'name': 'binary',
        'tag': 'bin',
        'description': 'program',
        'callable': False,
        'prepend': True,
    },
    {
        'name': 'program',
        'tag': 'bin',
        'description': 'program',
        'callable': False,
        'prepend': True,
    },
    {
        'name': 'dbcommand',
        'tag': 'dbcmd',
        'description': 'database command',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'expression',
        'tag': 'exp',
        'description': 'aggregation framework transformation expression',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'group',
        'tag': 'grp',
        'description': 'aggregation framework group expression',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'operator',
        'tag': 'op',
        'description': 'operator',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'query',
        'tag': 'op',
        'description': 'query',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'update',
        'tag': 'up',
        'description': 'update operator',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'parameter',
        'tag': 'param',
        'description': 'setParameter option',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'pipeline',
        'tag': 'pipe',
        'description': 'aggregation framework pipeline operator',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'projection',
        'tag': 'proj',
        'description': 'projection operator',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'method',
        'tag': 'meth',
        'description': 'shell method',
        'prepend': False,
        'callable': True,
    },
    {
        'name': 'authrole',
        'tag': 'auth',
        'description': 'user role',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'bsontype',
        'tag': 'bson',
        'description': 'BSON type',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'collflag',
        'tag': 'collflg',
        'description': 'collection flag',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'data',
        'tag': 'data',
        'description': 'MongoDB reporting output',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'error',
        'tag': 'err',
        'description': 'error code',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'limit',
        'tag': 'lmt',
        'description': 'MongoDB system limit',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'macro',
        'tag': 'mcr',
        'description': 'JavaScript shell macro',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'readmode',
        'tag': 'readpref',
        'description': 'read preference mode',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'setting',
        'tag': 'setting',
        'description': 'setting',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'replstate',
        'tag': 'replstate',
        'description': 'replica set state',
        'prepend': True,
        'callable': False,
    }
]

conf['prepend'] = { }

for directive in conf['directives']:
    if directive['prepend']:
        conf['prepend'][directive['name']] = directive['tag']
