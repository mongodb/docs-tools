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
        'tag': 'metaOp',
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
        'name': 'authaction',
        'tag': 'authr',
        'description': 'user action',
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
    },
    {
        'name': 'variable',
        'tag': 'variable',
        'description': 'system variable available in aggregation',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'writeconcern',
        'tag': 'writeconcern',
        'description': 'write concern values',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'readconcern',
        'tag': 'readconcern',
        'description': 'readConcern values',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'alert',
        'tag': 'alert',
        'description': 'system alert',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'event',
        'tag': 'event',
        'description': 'system event',
        'prepend': False,
        'callable': False,
    },
    {
        'name': 'rsconf',
        'tag': 'rsconf',
        'description': 'replica set configuration setting',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'serverstatus',
        'tag': 'serverstatus',
        'description': 'serverstatus data',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'urioption',
        'tag': 'urioption',
        'description': 'uri option',
        'prepend': True,
        'callable': False,
    },
    {
        ## Support defining mongotape's commands
        'name': 'toolcommand',
        'tag': 'toolcommand',
        'description': 'mongo tool command',
        'prepend': True,
        'callable': False,
    },
    {
        ## Support mongotape's command-specific options
        'name': 'commandoption',
        'tag': 'commandoption',
        'description': 'mongo tool command-specific option',
        'prepend': True,
        'callable': False,
    },
    ## Custom Setting Directives for MMS
    {
        'name': 'msetting',
        'tag': 'msetting',
        'description': 'Monitoring Agent Setting',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'bsetting',
        'tag': 'bsetting',
        'description': 'Backup Agent Setting',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'asetting',
        'tag': 'asetting',
        'description': 'Automation Agent Setting',
        'prepend': True,
        'callable': False,
    },
    {
        'name': 'apierror',
        'tag': 'apierror',
        'description': 'Error Code for Public API',
        'prepend': False,
        'callable': False,
    },
    ## Custom Directives for PHP Library Docs
    {
        'name': 'phpclass',
        'tag': 'phpclass',
        'description': 'PHP Library class',
        'prepend': True,
        'callable': False
    },
    {
        'name': 'phpmethod',
        'tag': 'phpmethod',
        'description': 'PHP Library method',
        'prepend': True,
        'callable': False
    },
    ## Custom Directives for Atlas Docs
    {
        'name': 'atlasrole',
        'tag': 'atlasrole',
        'description': 'Atlas user role',
        'prepend': False,
        'callable': False,
    },
    ## Custom Directives for expansions
    {
        'name': 'expansion',
        'tag': 'expansion',
        'description': 'Expansion',
        'prepend': False,
        'callable': False
    },
    ## For service actions
    {
        'name': 'action',
        'tag': 'action',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For s3 service actions
    {
        'name': 's3action',
        'tag': 's3',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For ses service actions
    {
        'name': 'sesaction',
        'tag': 'ses',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For slack service actions
    {
        'name': 'slackaction',
        'tag': 'slack',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For http service actions
    {
        'name': 'httpaction',
        'tag': 'http',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For twilio service actions
    {
        'name': 'twilioaction',
        'tag': 'twilio',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For slack service actions
    {
        'name': 'slackaction',
        'tag': 'slack',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },
    ## For mailgun service actions
    {
        'name': 'mailgunaction',
        'tag': 'mailgun',
        'description': 'Service Actions',
        'prepend': True,  
        'callable': False
    },

]

## If prepend: True, you can have a page title that match the directive.  For example, an operator X in a page with title X.  Otherwise, you can't have in page with same title and you'll get iddup as the reference.

conf['prepend'] = { }

for directive in conf['directives']:
    if directive['prepend']:
        conf['prepend'][directive['name']] = directive['tag']
