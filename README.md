# Introduction
This project teaches Docker some IPFS. IPFS is a global, versioned, peer-to-peer filesystem. IPFS combines good ideas from Git, BitTorrent, Kademlia, SFS, and the Web. It is like a single bittorrent swarm, exchanging git objects.
[https://github.com/ipfs/go-ipfs]

image2ipfs works only with images prduced docker >= 1.10. On the bright side, all post-1.6 dockers can pull from an ipfs-registry.

# How does it work?

image2ipfs takes an image archive produced using `docker save`.
The archive is extracted to a temp location then processed a bit. Finally, it is added to IPFS using `ipfs add -r`
(you need to have the ipfs binary in your `PATH`). For a simple busybox image
image2ipfs will produce something like this:
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

The answer is simple: using url rewriting.There is a trivial Go application that speaks the Registry v2 protocol but instead of serving the blobs and manifests it redirects
to an IPFS gateway of your choice.

When pulling REPO:latest (with REPO=busybox in this example), Docker daemon will issue (roughly) these requests:
```
GET /v2/
GET /v2/REPO/manifest/latest
GET /v2/REPO/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /v2/REPO/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /v2/REPO/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```

The Go app serves redirects to an IPFS gateway like so:
```
GET /ipfs/HASH/manifest/latest
GET /ipfs/HASH/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /ipfs/HASH/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /ipfs/HASH/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```


# Installation
```bash
$ git clone https://github.com/jvassev/image2ipfs

# this will install a python command so pyenv or virtualenv is recommended rather than sudo
$ make install

$ image2ipfs --version
0.1.0
```

# Running the registry
You can pull the official image from dockerhub. This example assumes the gateway is running on localhost. Consider using another gateway address as image2ipfs will serve redirects to it.

```
docker run -td --name ipfs-registry -e IPFS_GATEWAY=http://localhost:8080 --net host jvassev/ipfs-registry
```

Or build from source and skip Docker:
```bash
$ make install

$ image2ipfs server
2019/03/12 15:43:58 Using IPFS gateway http://127.0.0.1:8080
2019/03/12 15:43:58 Serving on :5000
```

# Synopsis

The client and server live in the same binary. You can find prebuilt releases for Linux, Mac and Windows on the Releases page. The command flags are compatible with the legacy Python version.

```
usage: image2ipfs [<flags>] <command> [<args> ...]

Flags:
      --help       Show context-sensitive help (also try --help-long and --help-man).
      --version    Show application version.
  -r, --registry="http://localhost:5000"
                   Registry to use when generating pull URL
  -n, --no-add     Don`t add to IPFS, just print directory
  -q, --quiet      Produce less output - just the final pullable image name
  -d, --debug      Leave workdir intact (useful for debugging)
  -i, --input="-"  Docker image archive to process, defaults to stdin. Use - to explicitly set stdin

Commands:
  help [<command>...]
    Show help.


  client [<flags>]
    Populate IPFS node with image data

    -r, --registry="http://localhost:5000"
                     Registry to use when generating pull URL
    -n, --no-add     Don`t add to IPFS, just print directory
    -q, --quiet      Produce less output - just the final pullable image name
    -d, --debug      Leave workdir intact (useful for debugging)
    -i, --input="-"  Docker image archive to process, defaults to stdin. Use - to explicitly set stdin

  server [<flags>]
    Run an IFPS-backed registry

    --gateway="http://127.0.0.1:8080"
                    IPFS gateway. It must be reachable by pulling clients
    --addr=":5000"  Listen address.
```

# Configure Docker

As usual add `--insecure-registry localhost:5000` to your docker daemon args. You need to put the `image2ipfs server` behind a reverse proxy if you want to do proper TLS termination.

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

$ image2ipfs --version
0.1.0

$ docker pull centos:7
7: Pulling from library/centos
a02a4930cb5d: Pull complete
Digest: sha256:184e5f35598e333bfa7de10d8fb1cebb5ee4df5bc0f970bf2b1e7c7345136426
Status: Downloaded newer image for centos:7

$ docker save centos:7 | image2ipfs
docker save centos:7 | /home/jvassev/more/gohome/bin/image2ipfs
2019/03/12 15:38:59 workdir is /tmp/image2ipfs887013748
2019/03/12 15:39:01 processing centos:7
2019/03/12 15:39:01 processing layer /tmp/image2ipfs887013748/9841c41d4b0d8fe3bf22b7c3c12e7633870218fffec04d84e7d62993ac175a19/layer.tar
2019/03/12 15:39:11 using ipfs in /home/jvassev/.bin/ipfs
2019/03/12 15:39:12 image ready Qmcsr3naQWG6YzeWTCa7Ee55JUqDdAwvo3j8VyAuRcrHvM
2019/03/12 15:39:12 browse image at http://localhost:8080/ipfs/Qmcsr3naQWG6YzeWTCa7Ee55JUqDdAwvo3j8VyAuRcrHvM
2019/03/12 15:39:12 dockerized hash ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq
2019/03/12 15:39:12 you can pull using localhost:5000/ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos
localhost:5000/ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos

# delete the image to make docker pull layers again
$ docker rmi centos:7
```

`image2ipfs` will produce a single line to stdout - the pullable docker image name. The rest is debug output you can suppress with `-q`.

```bash
$ docker pull localhost:5000/ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos
Using default tag: latest
latest: Pulling from ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos
Digest: sha256:4c7a24018edbcb72ec0e6a7ff6809db4aa2f306784bd79ab971e0497954ed4e2
Status: Downloaded newer image for localhost:5000/ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos:latest

$ docker history localhost:5000/ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq/centos
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
778a53015523        4 weeks ago         /bin/sh -c #(nop) CMD ["/bin/bash"]             0 B
<missing>           4 weeks ago         /bin/sh -c #(nop) LABEL name=CentOS Base Imag   0 B
<missing>           4 weeks ago         /bin/sh -c #(nop) ADD file:6dd89087d4d418ca0c   196.7 MB
<missing>           7 months ago        /bin/sh -c #(nop) MAINTAINER The CentOS Proje   0 B
```

Depending on how you have started the image2ipfs the docker daemon will be redirected to an IPFS gateway of your choice. By default the registry
will redirect to the ipfs daemon running locally (http://localhost:8080).

But what is this "dockerized hash ciqnqalrqxnqzubb2jllburc4e6wt2j7crjx2nxsdfbiw4sceq367lq" in the output?
Docker requires image names to be all lowercase which doesn't play nicely with base58-encoded binary. A dockerized IPFS hash
is just a base-32 of the same binary value. If you see a string starting with `ciq..` that's probably a dockerized IPFS hash.

In automated scenarios you'd probably want to run image2ipfs like this:
```bash

# build whatever images
$ docker built -t $TAG ...

# save the resulting image name
$ docker save $TAG | image2ipfs -q -r my-gateway.local:8080 > pull-url.txt
```

`-r my-gateway.local` instructs image2ipfs what pull url to produce. In a CI/CD you can distribute this generated url to downstream jobs that need to pull it.

# What's next

Not sure. It would be great if an IPFS gateway could speak the Registry v2 protocol  at /v2/* so you don't need to run a registry.

The Dockerized hash can be shortened a bit if base-36 is used instead of base-32/hex.


# Changelog

* 0.0.1: Broken, doesn't work
* 0.0.2: Works only with docker <= 1.9.1
* 0.0.3: Dockerized hash produced using base-32 (used to be hex/base-16)
* 0.0.4: Support for schema version 2 and docker > 1.10
* 0.0.5: image2ipfs: stop handling archives produced by docker < 1.10, ipfs-registry can still work with all post-1.6.x dockers
* 0.0.6: Deprecate manifest v1. Rewrite image2ipfs-server in golang
* 0.1.0: Rewrite image2ipfs in go: Single binary for client and server

# FAQ

> Why can't I use tags or references.

The tag is always "latest". The "real" reference is encoded in the name of the image, that is, the "dockerized hash". Even
if you export myimage:my-tag, in the IPFS registry you always tag "latest" but an image like ciq9a3eafb835d79e/myimage:latest.
This is very similar to how gx and gx-go work [https://github.com/whyrusleeping/gx].
