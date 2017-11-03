#!/usr/bin/env python3
import os
import re
import sys
import readline

PAT_EXISTING_HEADMATTER = re.compile(r'^\+\+\+[\s\S]+\+\+\+')

FILES = set(['sharding-tiered-hardware-for-varying-slas.md'])


def migrate(src: str, dest: str) -> None:
    with open(dest, 'r') as f:
        headmatter = PAT_EXISTING_HEADMATTER.match(f.read())
        assert headmatter is not None
        headmatter = headmatter.group(0)

    with open(src, 'r') as src_f:
        src_text = src_f.read()

    new_dest_text = PAT_EXISTING_HEADMATTER.sub(headmatter, src_text)
    new_dest_text = '\n'.join(l.rstrip() for l in new_dest_text.split('\n'))
    new_dest_text = new_dest_text.replace('”', '"').replace('“', '"').replace('’', '\'')
    with open(dest, 'w') as f:
        f.write(new_dest_text)


def main() -> None:
    src_dir_path = sys.argv[1]
    if os.path.isdir('../docs-tutorials'):
        dest_dir_path = '../docs-tutorials'
    else:
        dest_dir_path = input('Path to docs-tutorials: ')

    for root, _, files in os.walk(src_dir_path):
        for filename in files:
            src_path = os.path.join(root, filename)
            dest_path = os.path.join(dest_dir_path, 'content', filename)
            if os.path.isfile(dest_path):
                migrate(src_path, dest_path)


if __name__ == '__main__':
    main()
