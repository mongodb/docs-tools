import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from rstcloth import RstCloth
import utils

def generate_hash_file(fn):
    r = RstCloth()

    if os.path.exists(fn):
        with open(fn, 'r') as f:
            existing = f.read()
    else:
        existing = []

    commit = utils.get_commit()

    r.directive('|commit| replace', '``{0}``'.format(commit))

    try:
        if r.get_block('_all')[0] == existing[:-1]:
            print('[build]: no new commit(s), not updating {0} ({1})'.format(fn, commit))
            return True
    except TypeError:
        print('[ERROR] [build]: problem generating {0}, continuing'.format(fn))
        with file(fn, 'a'):
            os.utime(fn, times)
    else:
        r.write(fn)
        print('[build]: regenerated {0} with new commit hash: {1}'.format(fn, commit))

def main():
    fn = sys.argv[1]

    generate_hash_file(fn)

if __name__ == '__main__':
    main()
