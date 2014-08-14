# Copyright 2014 MongoDB, Inc.
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

import argh

from pharaoh.mongo_to_po import write_mongo_to_po_files
from pharaoh.po_to_mongo import put_po_files_in_mongo
from pharaoh.manage import runserver
from pharaoh.config.runtime import RuntimeStateConfig
from pharaoh.config.main import Configuration

logger = logging.getLogger('pharaoh.main')


######################### Operations ###################################

@argh.arg('--po', required=True, dest='po_files')
@argh.arg('--source_language', '-sl', default='en', dest='source_language')
@argh.arg('--target_language', '-tl', required=True, dest='target_language')
@argh.arg('--host', default=None, dest='host')
@argh.arg('--port', default=None, dest='port')
@argh.arg('--dbname', '-db', default=None, dest='db_name')
@argh.arg('--all', default=False, action='store_true', dest='all')
@argh.named('export-po')
def mongo_to_po(args):
    conf = fetch_config(args)
    if args.host is not None:
        host = args.host
    else:
        host = conf.MONGO_HOST
    if args.port is not None:
        port = args.port
    else:
        port = conf.MONGO_PORT
    if args.db_name is not None:
        db_name = args.db_name
    else:
        db_name = conf.MONGO_DBNAME
    
    write_mongo_to_po_files(args.po_files, args.source_language, args.target_language,
                            host, port, db_name, args.all)


@argh.arg('--po', required=True, dest='po_files')
@argh.arg('--username', '-u', required=True, dest='username')
@argh.arg('--status', '-s', default='SMT', dest='status')
@argh.arg('--source_language', '-sl', default='en', dest='source_language')
@argh.arg('--target_language', '-tl', required=True, dest='target_language')
@argh.arg('--host', default=None, dest='host')
@argh.arg('--port', default=None, dest='port')
@argh.arg('--dbname', '-db', default=None, dest='db_name')
@argh.named('import-po')
def po_to_mongo(args):
    conf = fetch_config(args)
    if args.host is not None:
        host = args.host
    else:
        host = conf.MONGO_HOST
    if args.port is not None:
        port = args.port
    else:
        port = conf.MONGO_PORT
    if args.db_name is not None:
        db_name = args.db_name
    else:
        db_name = conf.MONGO_DBNAME
    put_po_files_in_mongo(args.po_files, args.username, args.status,
                          args.source_language, args.target_language,
                          host, port, db_name)

@argh.arg('--host', default=None, dest='host')
@argh.arg('--port', default=None, dest='port')
def verifier(args):
    conf = fetch_config(args)
    if args.host is not None:
        host = args.host
    else:
        host = conf.SERVER_HOST
    if args.port is not None:
        port = args.port
    else:
        port = conf.SERVER_PORT
    runserver(conf, host, port)

########################## Setup #######################################


def get_base_parser():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')

    return parser

def fetch_config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    return c

############################ Entry Point #################################


def main():
    parser = get_base_parser()

    commands = [
        mongo_to_po,
        po_to_mongo,
        verifier,
    ]
    argh.add_commands(parser, commands)
    args = RuntimeStateConfig()

    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()
