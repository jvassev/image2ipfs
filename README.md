# Introduction
This project teaches Docker some IPFS. IPFS is a global, versioned, peer-to-peer filesystem. IPFS combines good ideas from Git, BitTorrent, Kademlia, SFS, and the Web. It is like a single bittorrent swarm, exchanging git objects.
[https://github.com/ipfs/go-ipfs]

image2ipfs works only with images prduced docker >= 1.10. On the bright side, all post-1.6 dockers can pull from an ipfs-registry.

# How does it work?

image2ipfs takes an image archive produced using `docker save`.
The archive is extracted to a temp location then processed a bit. Finally, it is added to IPFS using `ipfs add -r`
(you need to have the ipfs binary in your `PATH`). For a simple busybox image
image2ipfs will produce a work dir like this:
```
busybox
├── blobs
│   ├── sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
│   ├── sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
│   └── sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
└── manifests
    └── latest-v2
```

_v1 Manifests are not supported starting with version 0.0.6_
But how do you get from something like QmQSF1oN4TXeU2kRvmjerEs62ZYfKPyRCqPvW1XTTc4fLS to a working `docker pull busybox`?

The answer is simple: using url rewriting. In the `registry/` subdirectory of the project
there is a trivial Go application that speaks the Registry v2 protocol but instead of serving the blobs and manifests it redirects
to an IPFS gateway of your choice.

When pulling REPO:latest (with REPO=busybox in this example), Docker daemon will issue these requests:
```
GET /v2/
GET /v2/REPO/manifest/latest
GET /v2/REPO/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /v2/REPO/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /v2/REPO/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```

All the Go app does is produce IPFS links to a an IPFS gateway and redirect docker there:
```
GET /ipfs/HASH/manifest/latest
GET /ipfs/HASH/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /ipfs/HASH/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /ipfs/HASH/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```


# Installation
```bash
$ git clone https://github.com/jvassev/image2ipfs
$ cd image2ipfs

# this will install a python command so pyenv or virtualenv is recommended rather than sudo
$ make install

$ image2ipfs -v
0.0.6
```

You can also install using pip
```bash
$ pip install image2ipfs

$ image2ipfs -v
0.0.6
```

# Running the registry
You can pull the official image from dockerhub. This example assumes the gateway is running on localhost. Consider using another gateway address as image2ipfs will serve redirects to it.

```
docker run -td --name ipfs-registry -e IPFS_GATEWAY=http://localhost:8080 --net host jvassev/ipfs-registry
```

Or build from source:
```bash
# build image locally
make build-image

# or install to $GOPATH/bin
make install
```

# Configure Docker

As usual add `--insecure-registry localhost:5000` to your docker daemon args

# Demo
Assuming you have completed the steps above, let's publish a centos:7 image to IPFS!
```bash
$ docker version
Client:
 Version:      1.11.1
 API version:  1.23
 Go version:   go1.5.4
 Git commit:   5604cbe
 Built:        Tue Apr 26 23:38:55 2016
 OS/Arch:      linux/amd64

Server:
 Version:      1.11.1
 API version:  1.23
 Go version:   go1.5.4
 Git commit:   5604cbe-unsupported
 Built:        Sun May  1 20:27:17 2016
 OS/Arch:      linux/amd64

$ image2ipfs -v
0.0.6

$ docker pull centos:7
7: Pulling from library/centos
fa5be2806d4c: Pull complete
2ebc6e0c744d: Pull complete
044c0f15c4d9: Pull complete
28e524afdd05: Pull complete
Digest: sha256:b3da5267165bbaa9a75d8ee21a11728c6fba98c0944dfa28f15c092877bb4391
Status: Downloaded newer image for centos:7

$ docker save centos:7 | image2ipfs
Extracting to /tmp/tmpluDoZF
Preparing image in /tmp/tmp3iBMaF
	Processing centos@sha256:49dccac9d468cc1d3d9a3eafb835d79ed56b99c931ab232774d32b75d220d241
	Compressing layer /tmp/tmpluDoZF/768d4f50f65f00831244703e57f64134771289e3de919a576441c9140e037ea2/layer.tar
	Compressing layer /tmp/tmpluDoZF/da060eb693ac47689ca545355a060197bd2aadad76ca67535e95838de0737302/layer.tar
	Compressing layer /tmp/tmpluDoZF/a3f571afcd5241f02ca23fd50e45a403437d20ae3e215413d602e2deae3f86bc/layer.tar
	Compressing layer /tmp/tmpluDoZF/49dccac9d468cc1d3d9a3eafb835d79ed56b99c931ab232774d32b75d220d241/layer.tar
	Compressing layer /tmp/tmpluDoZF/49dccac9d468cc1d3d9a3eafb835d79ed56b99c931ab232774d32b75d220d241/layer.tar
	Compressing layer /tmp/tmpluDoZF/a3f571afcd5241f02ca23fd50e45a403437d20ae3e215413d602e2deae3f86bc/layer.tar
	Compressing layer /tmp/tmpluDoZF/da060eb693ac47689ca545355a060197bd2aadad76ca67535e95838de0737302/layer.tar
	Compressing layer /tmp/tmpluDoZF/768d4f50f65f00831244703e57f64134771289e3de919a576441c9140e037ea2/layer.tar
Image ready: QmdLmBErojQctCn9MHMV61BNA6ue2fyDZZAvFRF32cccTT
	Browse image at http://localhost:8080/ipfs/QmdLmBErojQctCn9MHMV61BNA6ue2fyDZZAvFRF32cccTT
	Dockerized hash ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq
	You can pull using localhost:5000/ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos
localhost:5000/ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos

# delete the image to make docker pull layers again
$ docker rmi centos:7
```

The last line contains the image name (you can get only it by passing `-q` to image2ipfs). If you have the IPFS registry
running you should be able to pull:

```bash
$ docker pull localhost:5000/ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos
Using default tag: latest
latest: Pulling from ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos
Digest: sha256:2c863897110a2aa59287df9e4544fb4d15f83b41e44ed578872e6314b1025a1e
Status: Image is up to date for localhost:5000/ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos:latest

$ docker history localhost:5000/ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq/centos
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
778a53015523        4 weeks ago         /bin/sh -c #(nop) CMD ["/bin/bash"]             0 B
<missing>           4 weeks ago         /bin/sh -c #(nop) LABEL name=CentOS Base Imag   0 B
<missing>           4 weeks ago         /bin/sh -c #(nop) ADD file:6dd89087d4d418ca0c   196.7 MB
<missing>           7 months ago        /bin/sh -c #(nop) MAINTAINER The CentOS Proje   0 B
```

Depending on how you have started the ipfs-registry the docker daemon will be redirected to an IPFS gateway of your choice. By default the registry
will redirect to the ipfs daemon running locally (http://localhost:8080).

But what is this "Dockerized hash ciqn5zu57ciucp3gw2hwxymuwz3tgjlvfdfwg3xhwx456y4xxydkhmq" in the output?
Docker requires image names to be all lowercase which doesn't play nicely with base58-encoded binary. A dockerized IPFS hash
is just a base-32 of the same binary value. This is the reason why the ipfs-registry is not a simple nginx+rewrite rules: you need
to do base-32 to base-58 conversions. If you see a string starting with `ciq` that's probably a dockerized ipfs hash.
(OK, you can also do this with nginx_lua)

In automated scenarios you'd probably want to run image2ipfs like this:
```bash

# build whatever images
$ docker built -t $TAG ...
$ docker save $TAG | image2ipfs -q -r my-gateway.local:9090 | tee pull-url.txt
my-gateway.local:9090/ciq..../centos
```

`-r my-gateway.local` instructs image2ipfs what pull url to produce. In a CI/CD you can distribute this generated url to downstream jobs that need to pull it.

# What's next

Not sure. It would be great if an IPFS gateway could speak the Registry v2 protocol  at /v2/* so you don't need to run a registry.

The Dockerized hash can be shortened a bit if base-36 is used instead of base-32/hex.

# Synopsis

```
usage: image2ipfs [-h] [--quiet] [--version] [--input INPUT] [--no-add]
                  [--registry REGISTRY]

optional arguments:
  -h, --help            show this help message and exit
  --quiet, -q           produce less output
  --version, -v         prints version
  --input INPUT, -i INPUT
                        Docker image archive to process, defaults to stdin
  --no-add, -n          Don`t add to IPFS, just print directory
  --registry REGISTRY, -r REGISTRY
                        Registry to use when generating pull URL

```

# Changelog

* 0.0.1: Broken, doesn't work
* 0.0.2: Works only with docker <= 1.9.1
* 0.0.3: Dockerized hash produced using base-32 (used to be hex/base-16)
* 0.0.4: Support for schema version 2 and docker > 1.10
* 0.0.5: image2ipfs: stop handling archives produced by docker < 1.10, ipfs-registry can still work with all post-1.6.x dockers
* 0.0.6: Deprecate manifest v1. Rewrite image2ipfs-server in golang

# FAQ

> Why can't I use tags or references.

The tag is always "latest". The "real" reference is encoded in the name of the image, that is, the "dockerized hash". Even
if you export myimage:my-tag, in the IPFS registry you always tag "latest" but an image like ciq9a3eafb835d79e/myimage:latest.
This is very similar to how gx and gx-go work [https://github.com/whyrusleeping/gx].
