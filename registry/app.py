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

import binascii
import os

import base58
from flask import Flask, Response

app = Flask(__name__)

gw = os.getenv('IPFS_GATEWAY')


@app.route('/v2/')
def hello():
    resp = Response('A docker registry that will redirect to an IPFS gateway')
    resp.headers.add('content-type', 'text/plain')
    resp.headers.add('Docker-Distribution-API-Version', 'registry/2.0')
    return resp


def ipfsy_digest(digest):
    bytes = binascii.a2b_hex(digest)
    return base58.b58encode(bytes)


@app.route('/v2/<string:digest>/<path:path>')
def content(digest, path):
    location = gw + '/ipfs/' + ipfsy_digest(digest) + '/' + path
    resp = Response(status=302)
    resp.headers.add('location', location)
    resp.headers.add('Docker-Distribution-API-Version', 'registry/2.0')
    return resp


if __name__ == '__main__':
    # ctx = ('server.crt', 'server.key')
    ctx = None
    app.run(host='0.0.0.0', ssl_context=ctx)
