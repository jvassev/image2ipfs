# Copyright 2016 Julian Vassev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

import base64
import json
import logging
import os
import sys
import wsgiref.simple_server

import base58
from flask import Flask, Response, request

MF_SCHEMA_V2_LIST = 'application/vnd.docker.distribution.manifest.v2+json'

MF_SCHEMA_V2 = 'application/vnd.docker.distribution.manifest.list.v2+json'

app = Flask(__name__)

gw = os.getenv('IPFS_GATEWAY', '')


@app.route('/v2/')
def hello():
    resp = Response(json.dumps({
        'what': 'A docker registry that will redirect to an IPFS gateway',
        'gateway': gw,
        'handles': [
            MF_SCHEMA_V2,
            MF_SCHEMA_V2_LIST
        ],
        'problematic': ['version 1 registries'],
        'project': 'https://github.com/jvassev/image2ipfs/'
    }), content_type='application/json')

    resp.headers.add('Docker-Distribution-API-Version', 'registry/2.0')
    return resp


@app.route('/v2/<string:digest>/<path:path>')
def content(digest, path):
    suf = ''

    if path.endswith('/latest'):
        # a request for a manifest
        accepts = request.headers.getlist('accept')
        suf = '-v1'

        # docker > 1.10, prefer v2 schema
        for a in accepts:
            if MF_SCHEMA_V2_LIST in a:
                suf = '-v2'
                break
            if MF_SCHEMA_V2 in a:
                suf = '-v2'
                break

    h = ipfsy_digest(digest)

    if suf != '':
        # manifest request, redirect to self just to be able to to set the content type
        location = '/ipfs/' + h + '/' + path + suf
    else:
        # blob request,
        location = gw + '/ipfs/' + h + '/' + path

    resp = Response(status=302)
    resp.headers.add('location', location)
    resp.headers.add('Docker-Distribution-API-Version', 'registry/2.0')
    return resp


def ipfsy_digest(digest):
    bytes = base64.b32decode(digest.upper() + '=')
    return base58.b58encode(bytes)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if gw == '':
        sys.stderr.write('Must set IPFS_GATEWAY env var\n')
        sys.exit(1)

    gw = gw.rstrip('/')

    httpd = wsgiref.simple_server.make_server('0.0.0.0', 4444, app)
    httpd.serve_forever()
