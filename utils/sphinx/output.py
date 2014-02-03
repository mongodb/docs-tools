import re
import os.path

from utils.config import lazy_conf

def output_sphinx_stream(out, builder, conf=None):
    if conf is None:
        conf = lazy_conf(conf)

    out = out.split('\n')

    full_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output)

    regx = re.compile(r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)')

    for l in out:
        if l == '':
            continue

        if builder.startswith('epub'):
            if l.startswith('WARNING: unknown mimetype'):
                continue
            elif len(l) == 0:
                continue
            elif l.startswith('WARNING: search index'):
                continue
            elif l.endswith('source/reference/sharding-commands.txt'):
                continue

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                continue

        if l.startswith(conf.paths.branch_output):
            l = os.path.join(conf.paths.projectroot, l[len(conf.paths.branch_output)+1:])
        elif l.startswith(full_path):
            l = os.path.join(conf.paths.projectroot, l[len(full_path)+1:])
        elif l.startswith('source'):
            l = os.path.join(conf.paths.projectroot, l)

        print(l)
