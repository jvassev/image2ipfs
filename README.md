# Introduction
This project teaches Docker some IPFS. IPFS is a global, versioned, peer-to-peer filesystem. It combines good ideas from Git, BitTorrent, Kademlia, SFS, and the Web. It is like a single bittorrent swarm, exchanging git objects.
[https://github.com/ipfs/go-ipfs]

This projects is tested with docker-1.9.1 and ipfs-0.4.1. It is known not to work with docker-1.11.1. However, image2ipfs
works with image archives produced by all versions of docker.

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
    └── latest
```

But how do you get from something like QmQSF1oN4TXeU2kRvmjerEs62ZYfKPyRCqPvW1XTTc4fLS to a working `docker pull busybox`?

The answer is simple: using url rewriting. In the `registry/` subdirectory of the project
there is a trivial Flask application that speaks the Registry v2 protocol but instead of serving the blobs and manifests it redirects
to an IPFS gateway of your choice.

When pulling REPO:latest (with REPO=busybox in this example), Docker daemon will issue these requests:
```
GET /v2/
GET /v2/REPO/manifest/latest
GET /v2/REPO/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /v2/REPO/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /v2/REPO/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```
So somehow you need encode the IPFS hash in `REPO`, then use it on the server to redirect to https://ipfs.io/ipfs/{HASH}/{NAME}/manifest/latest.
See Section "Full demo" bellow



# Installation
```bash
$ git clone https://github.com/jvassev/image2ipfs
$ cd image2ipfs

# this will install a python command so pyenv or virtualenv is recommended rather than sudo
$ make install

$ image2ipfs -v
0.0.1/c9673db.m
```
If someone else will be running an ipfs-registry then you can install image2ipfs using pip
```bash
$ pip install image2ipfs

$ image2ipfs -v

```

# Running the registry
```bash
cd image2ipfs/registry
make build run IPFS_GATEWAY=http://localhost:8080
```
This will start a flask application pretending to be a docker registry on http://localhost:5000

# Configure Docker
As usual add `--insecure-registry localhost:5000` to your docker daemon args

# Full demo
Assuming you have completed the steps above, let's publish a centos:7 image to IPFS!
```bash
$ docker version
Client:
 Version:      1.9.1
 API version:  1.21
 Go version:   go1.4.3
 Git commit:   a34a1d5
 Built:        Fri Nov 20 17:56:04 UTC 2015
 OS/Arch:      linux/amd64

Server:
 Version:      1.9.1
 API version:  1.21
 Go version:   go1.4.2
 Git commit:   a34a1d5
 Built:        Fri Nov 20 13:16:54 UTC 2015
 OS/Arch:      linux/amd64

$ image2ipfs -v
0.0.2

$ docker pull centos:7
7: Pulling from library/centos
fa5be2806d4c: Pull complete
2ebc6e0c744d: Pull complete
044c0f15c4d9: Pull complete
28e524afdd05: Pull complete
Digest: sha256:b3da5267165bbaa9a75d8ee21a11728c6fba98c0944dfa28f15c092877bb4391
Status: Downloaded newer image for centos:7

$ docker save centos:7 | image2ipfs
Saving stdin to temporary file
Extracting to /tmp/tmpPO9EY4
Preparing image in /tmp/tmp9PvL_7
	Processing centos@sha256:28e524afdd052cfa82227c67344c098aabcd51021dd1f3b0c71485abcdd78a86
	No manifest.json found, will build one
	Compressing layer /tmp/tmpPO9EY4/28e524afdd052cfa82227c67344c098aabcd51021dd1f3b0c71485abcdd78a86/layer.tar
	Compressing layer /tmp/tmpPO9EY4/044c0f15c4d9a7499734b75b73ea5754ceb2c1c22e86d7eaa5ab8098b60c5267/layer.tar
	Compressing layer /tmp/tmpPO9EY4/2ebc6e0c744d13008fac31bfffae2ebdbb04acd1a90bf63466496cd856e19365/layer.tar
	Compressing layer /tmp/tmpPO9EY4/fa5be2806d4c9aa0f75001687087876e47bb45dc8afb61f0c0e46315500ee144/layer.tar
Image ready: QmRhKG1VGPqEt3cwbehHWroqjhbC1izFCC4wudaJjRgrAk
	Browse image at http://localhost:8080/ipfs/QmRhKG1VGPqEt3cwbehHWroqjhbC1izFCC4wudaJjRgrAk
	Dockerized hash ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi
	You can pull using localhost:5000/ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos
localhost:5000/ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos

```

The last line is the most important (you can get only it by passing `-q` to image2ipfs). If you have the IPFS registry
running you should be able to pull:
```bash
$ docker pull localhost:5000/ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos
Using default tag: latest
latest: Pulling from ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos
9b8de281c9e8: Pull complete
aff4174d073b: Pull complete
36b68a688647: Pull complete
b624472cd074: Pull complete
Digest: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Status: Downloaded newer image for localhost:5000/ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos:latest

$ docker history localhost:5000/ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi/centos
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
b624472cd074        4 weeks ago         /bin/sh -c #(nop) CMD ["/bin/bash"]             0 B
36b68a688647        4 weeks ago         /bin/sh -c #(nop) LABEL name=CentOS Base Imag   0 B
aff4174d073b        4 weeks ago         /bin/sh -c #(nop) ADD file:6dd89087d4d418ca0c   196.7 MB
9b8de281c9e8        7 months ago        /bin/sh -c #(nop) MAINTAINER The CentOS Proje   0 B
```

Depending on how you have started the ipfs-registry you'd be redirected to an IPFS gateway of your choice. By default the registry
will redirect to the ipfs daemon running locally (http://localhost:8080).


But what is this "Dockerized hash ciqddxseacsddleyizojmahrh2uaq7ujnplse6r6mylurgu4bfodrmi" in the output?
Docker requires image names to be all lowercase which doesn't play nicely with base58-encoded binary. A dockerized IPFS hash
is just a base-32 of the same binary value. This is the reason why the ipfs-registry is not a simple nginx+rewrite rules: you need
to do base-32 to base-58 conversions. If you see a string starting with ciq that's probably a dockerized ipfs hash.

In automated scenarios you'd probably want to run image2ipfs like this:
```bash
$ docker built -t $TAG .
$ docker save $TAG | image2ipfs -q -r my-gateway.local | tee pull-url.txt
my-gw.local/ciq..../centos
```

`-r my-gateway.local` instructs image2ipfs what pull url to produce.
Then you can distribute the pull-url.txt to downstream jobs that need to pull the image.

# What's next
Not sure. It would be great if an IPFS gateway could speak the Registry v2 protocol so you don't need to run a registry.

Docker manifest schema 2 has arrived [https://docs.docker.com/registry/spec/manifest-v2-2/].
If the ipfs-registry understands the Accept header then it could serve the manifest version understood by docker daemon.
However, this requires changes to the ipfs gateway or running additional proxy on top of ipfs-gateway that takes care
of serving the right content and the right Content-Type headers. For now you are limited to using version 1 manifests and
docker-1.9.1.

When an image exported and processed both v1 and v2 versions of the manifests can be easily produced. The ipfs-registry then can
inspect the Accept header and redirect to either file. For this to work however, the manifests added to IPFS need the
mimeType metadata too.

The Dockerized hash can be shortened a bit if base-36 is used instead of base-16/hex.

# FAQ
> Why can't I use tags or references.

The tag is always "latest". The "real" reference is encoded in the name of the image, that is, the "dockerized hash". Even
if you export myimage:my-tag, in the ipfs registry you get just tag "latest" but an image like 9a3eafb835d79e/myimage:latest.
This is very similar to how gx and gx-go works [https://github.com/whyrusleeping/gx].