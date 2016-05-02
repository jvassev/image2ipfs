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
import base64
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
    parser.add_argument('--quiet', '-q', help='produce less output', action='store_true', default=False)
    parser.add_argument('--version', '-v', help='prints version', action='store_true')
    parser.add_argument('--input', '-i', help='Docker image archive to process, defaults to stdin. Use - for stdin',
                        default=None)
    parser.add_argument('--no-add', '-n', help='Don`t add to IPFS, just print directory', action='store_true')
    parser.add_argument('--registry', '-r', help='Registry to use when generating pull URL',
                        default='http://localhost:5000')

    args = parser.parse_args()
    command(args)


def command(args):
    if args.quiet:
        defaults._VERBOSE = False

    if args.version:
        print(defaults.DEBUG_VERSION)
        return

    if args.input is None or args.input == '-':
        f = sys.stdin
    else:
        f = open(args.input)

    temp = tempfile.mkdtemp()
    info("Extracting to " + temp)
    tar = tarfile.open(fileobj=f, mode='r|*')
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

    try:
        manifest = to_json(temp, 'manifest.json')[0]
        config = manifest['Config']
    except IOError:
        error('Image archive must be produced by docker > 1.10')

    config_dest = os.path.join(work, 'blobs', 'sha256:' + config[:-5])
    shutil.copyfile(os.path.join(temp, config), config_dest)

    mf = make_v2_manifest(config, config_dest, manifest, temp, work)
    write_pretty_json(mf, work, 'manifests', 'latest-v2')

    mf = make_v1_manifest(name, manifest, temp, os.path.join(work, 'blobs'))
    write_pretty_json(mf, work, 'manifests', 'latest-v1')
    return root, name


def make_v2_manifest(config, config_dest, manifest, temp, work):
    """produce v2 manifest of type application/vnd.docker.distribution.manifest.v2+json"""
    v2manifest = prepare_v2_manifest(manifest, temp, os.path.join(work, 'blobs'))
    v2manifest['config']['digest'] = 'sha256:' + config[:-5]
    v2manifest['config']['size'] = file_size(config_dest)
    return v2manifest


def write_pretty_json(obj, *path):
    with open(os.path.join(*path), 'w') as f:
        f.write(pretty_json(obj))


def dockerize_hash(hash):
    """base58 -> base32 conversion. strips padding"""
    byte_arr = base58.b58decode(hash)
    return base64.b32encode(byte_arr)[0:-1].lower()


def add_ipfs(work, registry, image):
    """invoke "ipfs -r" on work. No error checking. Returns a pullable string"""
    proc = subprocess.Popen(['ipfs', 'add', '-r', '-q', work], stdout=subprocess.PIPE)
    stdout = proc.communicate()[0]
    h = ''
    for line in stdout.splitlines():
        if line != '':
            h = line

    info("Image ready: " + h)
    info("\tBrowse image at http://localhost:8080/ipfs/" + h)

    h = dockerize_hash(h)
    info("\tDockerized hash " + h)

    # remove host/port/proto part from image name
    i = registry.find('//')
    if i >= 0:
        registry = registry[i + 2:]

    if registry[-1] != '/':
        registry += '/'

    pull = registry + h + '/' + image
    info("\tYou can pull using " + pull)

    print(pull)


def read_file(path):
    """reads a file to string"""
    with open(path, 'r') as f:
        return f.read()


def make_v1_manifest(name, mf, temp, blob_dir):
    """produce v1 manifest"""
    res = collections.OrderedDict()
    res['schemaVersion'] = 1
    res['name'] = name
    res['tag'] = 'latest'
    res['architecture'] = 'amd64'
    fsLayers = res['fsLayers'] = []
    history = res['history'] = []
    res['signatures'] = []

    for layer in reversed(mf['Layers']):
        layer_record = {}
        size, digest = compress_layer(os.path.join(temp, layer), blob_dir)
        layer_record['blobSum'] = 'sha256:' + digest
        fsLayers.append(layer_record)

        hist_record = {}
        hist_record['v1Compatibility'] = read_file(os.path.join(temp, layer).replace('/layer.tar', '/json'))
        history.append(hist_record)

    return res


def prepare_v2_manifest(mf, temp, blob_dir):
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
    """pretty-prints a jsn object"""
    return json.dumps(obj, indent=2)


def to_json(*path):
    """buils a full path and reads it as json"""
    with open(os.path.join(*path), 'r') as f:
        return json.load(f)


def simplify_name(name):
    """Remove host/port part from an image name"""
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
