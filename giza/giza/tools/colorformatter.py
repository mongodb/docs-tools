# Copyright 2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging


class ColorFormatter(logging.Formatter):
    """Logging formatter using VT100 terminal color codes."""
    VT100 = {
        'red': '31',
        'yellow': '33',
        'bright': '1'
    }

    COLORS = {
        logging.WARNING: ('yellow',),
        logging.ERROR: ('red', 'bright'),
        logging.CRITICAL: ('red', 'bright'),
    }

    def __init__(self, fmt='%(levelname)s:%(name)s:%(message)s', color=True):
        """Create a pretty-printing logging formatter. If color is True, use
           VT100 color codes to colorify output."""
        logging.Formatter.__init__(self, fmt=fmt)
        self.color = color

    def format(self, record):
        # If the "lean" option is given, don't include any additional information
        msg = logging.Formatter.format(self, record)
        if getattr(record, 'lean', False):
            msg = record.msg

        if not self.color:
            return msg

        composite = []
        for option in self.COLORS.get(record.levelno, ()):
            composite.append('{0}'.format(self.VT100[option]))

        return '\x1b[{0}m{1}\x1b[0m'.format(';'.join(composite), msg)
