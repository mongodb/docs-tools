import sys
import os.path

try:
    from utils.rstcloth.rstcloth import RstCloth
    from utils.git import get_commit
except ImportError:
    from ..rstcloth.rstcloth import RstCloth
    from ..git import get_commit

def generate_hash_file(fn):
    r = RstCloth()

    if os.path.exists(fn):
        with open(fn, 'r') as f:
            existing = f.read()
    else:
        existing = []

    commit = get_commit()

    r.directive('|commit| replace', '``{0}``'.format(commit))

    try:
        if r.get_block('_all')[0] == existing[:-1]:
            print('[build]: no new commit(s), not updating {0} ({1})'.format(fn, commit[:10]))
            return True
    except TypeError:
        print('[ERROR] [build]: problem generating {0}, continuing'.format(fn))
        with file(fn, 'a'):
            os.utime(fn, times)
    else:
        r.write(fn)
        print('[build]: regenerated {0} with new commit hash: {1}'.format(fn, commit[:10]))
