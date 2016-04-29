#!/usr/bin/env python

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
# limitations under the License.

import argparse
import binascii
import collections
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

import base58

import defaults


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quiet', '-q', help='Produce less output', action='store_true', default=False)
    parser.add_argument('--version', '-v', help='Prints version', action='store_true')
    parser.add_argument('--input', '-i', help='Docker image archive, defaults to stdin', default=None)
    parser.add_argument('--no-add', '-n', help='Don`t add to IPFS, just print directory', action='store_true')
    parser.add_argument('--registry', '-r', help='Registry to use when generating pull URL',
                        default='http://localhost:5000')

    args = parser.parse_args()
    command(args)


def command(args):
    if args.version:
        print(defaults.DEBUG_VERSION)
        return

    if args.input == None:
        error('Stdin not supported yet, must provide -i flag')
    else:
        f = open(args.input)

    if args.quiet:
        defaults._VERBOSE = False

    temp = tempfile.mkdtemp()
    info("Extracting to " + temp)
    tar = tarfile.TarFile(fileobj=f)
    tar.extractall(temp)

    work, image = process(temp)

    if args.no_add:
        print(work)
        return

    add_ipfs(work, args.registry, image)


def process(temp):
    root = work = tempfile.mkdtemp()
    info('Preparing image in ' + work)

    repos = to_json(temp, 'repositories')
    if len(repos) != 1:
        error('Only one repository expected in input file')

    name, tags = repos.iteritems().next()
    if len(tags) != 1:
        error('Only one tag expected for ' + name)

    image = tags.itervalues().next()
    info('\tProcessing ' + name + '@sha256:' + image)
    name = simplify_name(name)

    work = os.path.join(work, name)
    os.makedirs(os.path.join(work, 'manifests'))
    os.makedirs(os.path.join(work, 'blobs'))

    manifest = to_json(temp, 'manifest.json')[0]
    config = manifest['Config']
    config_dest = os.path.join(work, 'blobs', 'sha256:' + config[:-5])
    shutil.copyfile(os.path.join(temp, config), config_dest)

    v2manifest = make_manifest(manifest, temp, os.path.join(work, 'blobs'))
    v2manifest['config']['digest'] = 'sha256:' + config[:-5]
    v2manifest['config']['size'] = file_size(config_dest)

    v2manifest_dest = os.path.join(work, 'manifests', 'latest')
    with open(v2manifest_dest, 'w') as f:
        f.write(pretty_json(v2manifest))

    return root, name


def dockerize_hash(hash):
    bytes = base58.b58decode(hash)
    return binascii.b2a_hex(bytes)


def add_ipfs(work, registry, image):
    proc = subprocess.Popen(['ipfs', 'add', '-r', '-q', work], stdout=subprocess.PIPE)
    stdout = proc.communicate()[0]
    hash = ''
    for line in stdout.splitlines():
        if line != '':
            hash = line

    if registry[-1] != '/':
        registry += '/'

    info("Image ready: " + hash)
    info("\tBrowse image at http://localhost:8080/ipfs/" + hash)

    hash = dockerize_hash(hash)
    info("\tDockerized hash " + hash)

    i = registry.find('//')
    if i >= 0:
        registry = registry[i + 2:]

    pull = registry + hash + '/' + image
    info("\tYou can pull using " + pull)

    print(pull)


def make_manifest(mf, temp, blob_dir):
    res = collections.OrderedDict()
    res['schemaVersion'] = 2
    res['mediaType'] = 'application/vnd.docker.distribution.manifest.v2+json'

    config = res['config'] = collections.OrderedDict()
    config['mediaType'] = 'application/vnd.docker.container.image.v1+json'
    config['size'] = -1
    config['digest'] = ''

    layers = res['layers'] = []

    mediaType = 'application/vnd.docker.image.rootfs.diff.tar.gzip'
    for layer in mf['Layers']:
        obj = collections.OrderedDict()
        obj['mediaType'] = mediaType
        size, digest = compress_layer(os.path.join(temp, layer), blob_dir)
        obj['size'] = size
        obj['digest'] = 'sha256:' + digest
        layers.append(obj)

    return res


def compress_layer(path, blob_dir):
    info('\tCompressing layer ' + path)
    temp = os.path.join(blob_dir, 'layer.tmp.tgz')

    with open(path, 'rb') as f_in:
        with open(temp, 'wb') as f_out:
            # produce deterministic gzip files
            gz = gzip.GzipFile(filename='', mode='wb', fileobj=f_out, mtime=0)
            gz.writelines(f_in)
            gz.close()

    digest = sha256_file(temp)
    size = file_size(temp)
    os.rename(temp, os.path.join(blob_dir, 'sha256:' + digest))
    return size, digest


def file_size(path):
    return os.path.getsize(path)


def sha256_file(filename, blocksize=16 * 1024):
    hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            hash.update(block)
    return hash.hexdigest()


def pretty_json(obj):
    return json.dumps(obj, indent=2)


def to_json(*path):
    with open(os.path.join(*path), 'r') as f:
        return json.load(f)


def simplify_name(name):
    i = name.find('/')
    if i < 0:
        return name
    maybe_url = name[:i]
    if '.' in maybe_url or ':' in maybe_url:
        return name[i + 1:]

    return name


def info(msg):
    if defaults._VERBOSE:
        sys.stderr.write(msg + '\n')


def error(msg, code=1):
    sys.stderr.write('Error: ' + msg + '\n')
    sys.exit(code)


if __name__ == '__main__':
    main()
