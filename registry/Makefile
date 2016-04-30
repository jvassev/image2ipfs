TAG ?= $(shell git describe --match 'v[0-9]*' --dirty='.m' --always)
IMAGE ?= ipfs-registry
CONT ?= $(IMAGE)
IPFS_GATEWAY ?= http://localhost:8080

build:
	docker build -t $(IMAGE):$(TAG) .
	docker tag -f   $(IMAGE):$(TAG) $(IMAGE):latest

shell:
	@docker run --rm -ti -u root -v `pwd`:/src --entrypoint=/bin/bash $(IMAGE)

push: build
	docker tag -f $(IMAGE):$(TAG) $(REMOTE)/$(IMAGE):$(TAG)
	docker push $(REMOTE)/$(IMAGE):$(TAG)

attach:
	@docker exec -ti $(CONT)  /bin/bash

stop:
	@(docker stop -t 1 $(CONT)   && docker rm $(CONT)  )  || true

logs:
	@docker logs -f $(CONT)

run: stop build
	docker run -ti --name $(CONT) \
		$(EXTRA_ARGS) \
		--net=host \
		-e IPFS_GATEWAY=$(IPFS_GATEWAY) \
		$(IMAGE):latest
