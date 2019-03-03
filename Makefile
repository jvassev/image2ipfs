TAG               ?= latest
IMAGE             ?= jvassev/ipfs-registry
DOCKER_BUILD_ARGS ?=

IPFS_GATEWAY ?= http://localhost:8080

dist: version
	python setup.py sdist

lint:
	cd image2ipfs && pylint --rcfile pylint.rc *.py

test:
	cd image2ipfs && python -m unittest discover


clean:
	rm -fr image2ipfs/*.pyc
	rm -fr dist/ build/ *.egg-info

install: clean version
	python setup.py install
	image2ipfs --version

version:
	@git describe --match 'v[0-9]*' --dirty='.m' --always > image2ipfs/git-revision
	@cat image2ipfs/git-revision

upload: clean
	python setup.py sdist upload


build-image:
	docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE):$(TAG) -f image2ipfs-server/Dockerfile .
	docker tag    $(IMAGE):$(TAG) $(IMAGE):latest

shell:
	docker run --rm -ti -u root -v `pwd`:/workspace --entrypoint=/bin/sh $(IMAGE)

push-image: build-image
	docker push $(IMAGE):$(TAG)

attach:
	@docker exec -ti $(CONT)  /bin/bash

guess-tag:
	@echo TAG=`git describe --match 'v[0-9]*' --dirty='.m' --always`

install-server:
	CGO_ENABLED=0 go install github.com/jvassev/image2ipfs/image2ipfs-server

run-server: build-image
	docker run -ti --rm \
		--net=host \
		$(IMAGE):$(TAG)
