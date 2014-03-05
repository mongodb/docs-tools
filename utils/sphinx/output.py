import re
import os.path

from utils.config import lazy_conf

def output_sphinx_stream(out, conf=None):
    if conf is None:
        conf = lazy_conf(conf)

    out = [ o for o in out.split('\n') if o != '' ] 

    full_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output)

    regx = re.compile(r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)')

    printable = []
    for idx, l in enumerate(out):
        if is_msg_worthy(l) is not True:
            printable.append(None)
            continue

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                printable.append(None)
                continue

        l = path_normalization(l, full_path, conf)

        if l.startswith('InputError: [Errno 2] No such file or directory'):
            l = path_normalization(l.split(' ')[-1].strip()[1:-2], full_path, conf)
            printable[idx-1] += ' ' + l
            l = None

        printable.append(l)

    printable = list(set(printable))
    printable.sort()

    print_build_messages(printable)

def print_build_messages(messages):
    for l in ( l for l in messages if l is not None ):
        print(l)

def path_normalization(l, full_path, conf):
    if l.startswith(conf.paths.branch_output):
        l = l[len(conf.paths.branch_output)+1:]
    elif l.startswith(full_path):
        l = l[len(full_path)+1:]

    if l.startswith('source'):
        l = os.path.sep.join(['source', l.split(os.path.sep, 1)[1]])

    if conf.project.name == 'mms':
        if l.startswith('source-saas'):
            l = l.replace('source-saas', 'source')
        elif l.startswith('source-hosted'):
            l = l.replace('source-hosted', 'source')
        

    return l

def is_msg_worthy(l):
    if l.startswith('WARNING: unknown mimetype'):
        return False
    elif len(l) == 0:
        return False
    elif l.startswith('WARNING: search index'):
        return False
    elif l.endswith('source/reference/sharding-commands.txt'):
        return False
    else:
        return True
