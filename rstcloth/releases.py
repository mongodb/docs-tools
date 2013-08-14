#!/usr/bin/python

import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.getcwd())))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
from conf import release

from rstcloth import RstCloth

def cli():
    parser = argparse.ArgumentParser('Generate install files.')
    parser.add_argument(choices=['linux-i686', 'linux-x86_64', 'osx-x86_64'], dest='builder')
    parser.add_argument(choices=['core', 'amz64', 'rhel62', 'ubuntu1104', 'ubuntu1204', 'suse11'], dest='release')
    parser.add_argument(dest='output')

    p = parser.parse_args()

    if p.builder == 'linux-i686':
        builder = 'linux-i686'
        platform = 'linux'
    elif p.builder == 'linux-x86_64':
        builder = 'linux-x86_64'
        platform = 'linux'
    elif p.builder == 'osx-x86_64':
        builder = 'osx-x86_64'
        platform = 'osx'

    if p.release == 'core':
        release = 'core'
    if p.release == 'amz64':
        release = 'amzn64'
    elif p.release == 'rhel62':
        release = 'rhel62'
    elif p.release == 'ubuntu1104':
        release = 'ubuntu1104'
    elif p.release == 'ubuntu1204':
        release = 'ubuntu1204'
    elif p.release == 'suse11':
        release = 'suse11'

    return  { 'outputfile': p.output, 'builder': builder, 'platform': platform, 'release': release }

def generate_output(builder, platform, version, release):
    """ This is the legacy version of the function used by the makefile and CLI infrastructure"""

    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    if release == 'core':
        r.content('curl http://downloads.mongodb.org/{0}/mongodb-{1}-{2}.tgz > mongodb.tgz'.format(platform, builder, version), 3, wrap=False, block='cmd')
    else:
        r.content('curl http://downloads.10gen.com/linux/mongodb-{0}-subscription-{1}-{2}.tgz > mongodb.tgz'.format(builder, release, version), 3, wrap=False, block='cmd')
        r.content('tar -zxvf mongodb.tgz', 3, wrap=False, block='cmd')
        r.content('cp -R -n mongodb-{0}-subscription-{1}-{2}/ mongodb'.format(builder, release, version), 3, wrap=False, block='cmd')

    r.newline(block='footer')

    return r

def generate_release_output(builder, platform, architecture):
    """ This is the contemporary version of the function used by the generate.py script"""

    r = RstCloth()

    r.directive('code-block', 'sh', block='header')
    r.newline(block='header')

    if architecture == 'core':
        r.content('curl http://downloads.mongodb.org/{0}/mongodb-{1}-{2}.tgz > mongodb.tgz'.format(platform, builder, release), 3, wrap=False, block='cmd')
    else:
        r.content('curl http://downloads.10gen.com/linux/mongodb-{0}-subscription-{1}-{2}.tgz > mongodb.tgz'.format(builder, architecture, release), 3, wrap=False, block='cmd')
        r.content('tar -zxvf mongodb.tgz', 3, wrap=False, block='cmd')
        r.content('cp -R -n mongodb-{0}-subscription-{1}-{2}/ mongodb'.format(builder, architecture, release), 3, wrap=False, block='cmd')

    r.newline(block='footer')

    return r

def main():
    interface = cli()

    r = generate_output(interface['builder'], interface['platform'], release, interface['release'])

    r.write(interface['outputfile'])

if __name__ == '__main__':
    main()
