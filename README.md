# Introduction
This project teaches Docker some IPFS. IPFS is a global, versioned, peer-to-peer filesystem. It combines good ideas from Git, BitTorrent, Kademlia, SFS, and the Web. It is like a single bittorrent swarm, exchanging git objects.
[https://github.com/ipfs/go-ipfs]

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

The answer is simple: using a simple form of url rewriting. In the registry/ subdirectory on the project
there is a simplistic Flask application that speaks the Registry v2 protocol but instead of serving the blobs and manifests it redirects
to an IPFS gateway of your choice.

When pulling REPO:latest (with REPO=busybox in this example), Docker daemon will issue these requests:
```
GET /v2/
GET /v2/REPO/manifest/latest
GET /v2/REPO/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
GET /v2/REPO/blobs/sha256:193bda8d9ac77416619eb556391a9c5447adb2abf12aab515d1b0c754637eb80
GET /v2/REPO/blobs/sha256:a1b1b81d3d1afdb8fe119b002318c12c20934713b9754a40f702adb18a2540b9
```
So somehow you need encode the IPFS hash in `REPO`, then use it on the server to redirect to https://ipfs.io/ipfs/`HASH`/`NAME`/manifest/latest.
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
make build run IPFS_GATEWAY=https://ipfs.io
```
This will start a flask application pretending to be a docker registry on http://localhost:5000

# Configure Docker
As usual add `--insecure-registry localhost:5000` to your docker daemon args

# Full demo
Assuming you have completed the steps above, let's publish a centos:7 image to IPFS!
```
$ docker pull centos:7
7: Pulling from library/centos
a3ed95caeb02: Pull complete
5989106db7fb: Pull complete
Digest: sha256:b3da5267165bbaa9a75d8ee21a11728c6fba98c0944dfa28f15c092877bb4391
Status: Downloaded newer image for centos:7

$ docker save centos:7 > /tmp/centos-7.tar

$ image2ipfs -i /tmp/centos-7.tar
Extracting to /tmp/tmpWSpwMk
Preparing image in /tmp/tmp6EL22N
	Processing centos@sha256:49dccac9d468cc1d3d9a3eafb835d79ed56b99c931ab232774d32b75d220d241
	Compressing layer /tmp/tmpWSpwMk/768d4f50f65f00831244703e57f64134771289e3de919a576441c9140e037ea2/layer.tar
	Compressing layer /tmp/tmpWSpwMk/da060eb693ac47689ca545355a060197bd2aadad76ca67535e95838de0737302/layer.tar
	Compressing layer /tmp/tmpWSpwMk/a3f571afcd5241f02ca23fd50e45a403437d20ae3e215413d602e2deae3f86bc/layer.tar
	Compressing layer /tmp/tmpWSpwMk/49dccac9d468cc1d3d9a3eafb835d79ed56b99c931ab232774d32b75d220d241/layer.tar
Image ready: QmSb4z96f6UGmkqtb1z3DJEyQsJzpshMMsqtuhcDbch2nS
	Browse image at http://localhost:8080/ipfs/QmSb4z96f6UGmkqtb1z3DJEyQsJzpshMMsqtuhcDbch2nS
	Dockerized hash 12203f2054184ef2f726c21538c28e1c14c36a6026e2087c2b6602816fadb95ecc9f
	You can pull using localhost:5000/12203f2054184ef2f726c21538c28e1c14c36a6026e2087c2b6602816fadb95ecc9f/centos
localhost:5000/12203f2054184ef2f726c21538c28e1c14c36a6026e2087c2b6602816fadb95ecc9f/centos

```

The last line is the most important (you can get only it by passing `-q` to image2ipfs). If you have the IPFS registry
running you should be able to pull:
```
docker pull localhost:5000/12203f2054184ef2f726c21538c28e1c14c36a6026e2087c2b6602816fadb95ecc9f/centos
```

Depending on how you have started the ipfs-registry you'd be redirected to an IPFS gateway of your choice. Docker requires https
so you may not be able to use your local daemon at http://localhost:8080.


But what is this "Dockerized hash 12203f2054184ef2f726c21538c28e1c14c36a6026e2087c2b6602816fadb95ecc9f" in the output?
Docker requires image names to be all lowercase which doesn't play nicely with base58-encoded binary. A dockerized IPFS hash
is just a hex-encoding of the same hash. This is the reason why the ipfs-registry is not a simple nginx+rewrite rules: you need
to do base-16 to base-58 conversions.

# What's next
Not sure. It would be great if an IPFS gateway could speak the Registry v2 protocol so you don't need to run a registry.

# FAQ
> Why can't I use tags or references.

The tag is always "latest". The "real" reference is encoded in the name of the image, that is, the "dockerized hash". Even
if you export myimage:my-tag, in the ipfs registry you get just tag "latest" but an image like 9a3eafb835d79e/myimage:latest.
This is very similar to how gx and gx-go works [https://github.com/whyrusleeping/gx].