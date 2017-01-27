#!/usr/bin/env python3
import re
import os
import sys
import yaml
import json
import logging
from typing import Dict, List, Optional

PAT_DIRECTIVE = re.compile(r'^([^\S\n]*).. test::\s*(\w*)$', re.M)
logger = logging.getLogger('doctest')


class Block:
    __slots__ = ('filename', 'lineno', 'code', 'check',
                 'description', 'language')

    def __init__(self, filename: str, lineno: int, code: str, check: str,
                       description: str, language: str) -> None:
        self.filename = filename
        self.lineno = lineno
        self.code = code
        self.check = check
        self.description = description
        self.language = language

    def serialize(self) -> Dict[str, object]:
        return {
            'filename': self.filename,
            'lineno': self.lineno,
            'code': self.code,
            'check': self.check,
            'description': self.description,
            'language': self.language
        }


class Doctest:
    def __init__(self, root: str) -> None:
        self.root = root

    def crawl(self) -> List[Block]:
        """Scan this instance's root directory for doc-"""
        blocks = []  # type: List[Block]

        for root, _, files in os.walk(self.root):
            for filename in files:
                if not filename.endswith('.rst') and not filename.endswith('.txt'):
                    continue

                path = os.path.join(root, filename)

                try:
                    blocks.extend(self.process_file(path))
                except yaml.scanner.ScannerError:
                    logger.exception('Error parsing YAML in %s', path)

        return blocks

    def process_file(self, path: str) -> List[Block]:
        blocks = []  # type: List[Block]
        output_lines = []  # type: List[str]

        path = os.path.abspath(path)
        with open(path) as f:
            file_text = f.read()

        for match in PAT_DIRECTIVE.finditer(file_text):
            indentation = match.group(1) + '   '
            language = match.group(2)
            pat = re.compile('(?:^{}[^\n]*\n)+'.format(indentation), re.M)
            block_match = pat.search(file_text, match.end(0))
            directive_text = block_match.group(0)

            data = yaml.safe_load(directive_text)
            code = data.get('code', '')
            check = data.get('check', '')
            lineno = file_text.count('\n', 0, match.start(0)) + 1
            description = data.get('description', None)

            blocks.append(Block(filename=path, lineno=lineno, code=code,
                                check=check, description=description,
                                language=language))

        return blocks


def main(args: List[str]) -> None:
    outpath = args[2]
    doctest = Doctest(args[1])
    blocks = doctest.crawl()
    raw_blocks = [b.serialize() for b in blocks]

    with open(outpath, 'w') as f:
        f.write(json.dumps(raw_blocks, indent=2))

if __name__ == '__main__':
    main(sys.argv)
