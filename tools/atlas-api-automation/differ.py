#!/usr/bin/env python3
import json
import os
import pprint
import re
import sys
from typing import List, Dict

pp = pprint.PrettyPrinter(indent=4)

# the json file of endpoints generated from the latest atlas code
ATLAS_JSON_FILE = './mms.api.json'
OUTPUT_FILE = './diff_list.txt'
WHITELIST_FILE = './whitelist.txt'

# this is the regex that will look in the contents of atlas reference
# api files and try to find the endpoints
# e.g.  in "/source/reference/api/process-measurements.txt" it will match the line:
#       GET api/atlas/v1.0/groups/{GROUP-ID}/processes/{HOST}:{PORT}/measurements
ROUTE_REGEX = r'(?:POST|GET|DELETE|PATCH) (?:\/.*|api.*)'


def main(args: List[str]) -> None:
    # must provide path to local cloud-docs dir
    if len(args) == 0:
        print('Please provide a path to the cloud-docs directory.')
        exit(1)

    ATLAS_API_REFERENCE = args[0] + '/source/reference/api/'

    # cloud-docs dir provided must contain api files
    if not os.path.isdir(ATLAS_API_REFERENCE):
        err = '''\nThe path: \n{apiref}\ndoes not contain a list of reference api files for atlas.
        '''.format(apiref=ATLAS_API_REFERENCE)
        print(err)
        exit(1)

    # get files in reference api directory for atlas
    api_files = [
        file for file in os.listdir(ATLAS_API_REFERENCE)
        if os.path.isfile(os.path.join(ATLAS_API_REFERENCE, file))
    ]

    # will do a diff on these lists to see what new endpoints have not been documented yet
    atlas_endpoints_in_docs = {}
    atlas_endpoints_diff_from_docs = []

    # store endpoints we currently have for atlas docs in dictionary
    for api_file in api_files:
        with open(ATLAS_API_REFERENCE + api_file) as file_contents:
            match = re.search(ROUTE_REGEX, file_contents.read())
            # continue if no regex match found
            if not match:
                continue
            # if API route was found in text, replace base url and params with wildcard chars
            route_string = re.sub(r'(\/?api\/atlas\/v1\.0)', '', match.group())
            route_string = re.sub(r'{.+?}', '{*}', route_string)
            route_string = route_string.replace('{*}:{*}', '{*}')
            # some routes end with a trailing slash and so correct routes won't match
            # e.g. 'GET /orgs/{*}/invoices' will not match 'GET /orgs/{*}/invoices/'
            if route_string.endswith('/'):
                route_string = route_string[:-1]
            atlas_endpoints_in_docs[route_string] = True

    # get whitelist of endpoints that we've deemed OK and do not include in output
    with open(WHITELIST_FILE) as whitelist:
        skip_endpoints = set(whitelist.read().splitlines())

    # get json data of latest atlas code
    with open(ATLAS_JSON_FILE) as atlas_json:
        data = json.load(atlas_json)
        for route in data:
            route_path = route['path']
            # if this endpoint is not part of atlas
            if 'atlas' not in route_path:
                continue
            # this is an atlas endpoint, so parse the object
            route_path = route_path.replace('/api/atlas/v1.0', '')
            route_path = route_path.replace('/api/{app:public|atlas}/v1.0', '')
            route_path = re.sub('{.+?}', '{*}', route_path)
            # empty endpoint string just skip it
            if route_path == '':
                continue
            route_string = route['method'] + ' ' + route_path
            if route_string not in atlas_endpoints_in_docs and route_string not in skip_endpoints:
                atlas_endpoints_diff_from_docs.append(route_string)

    # save the diff list to a file
    with open(OUTPUT_FILE, 'w') as out_file:
        out_file.write('\n'.join(atlas_endpoints_diff_from_docs))

    output_string = '''
        Found {numdiff} differences between Atlas code and current docs.
        List written to {outfile}
    '''.format(numdiff=len(atlas_endpoints_diff_from_docs), outfile=OUTPUT_FILE)
    print(output_string)


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
