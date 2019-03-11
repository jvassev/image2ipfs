TAG               ?= latest
IMAGE             ?= jvassev/ipfs-registry
DOCKER_BUILD_ARGS ?=
PKG               := github.com/jvassev/image2ipfs
IPFS_GATEWAY      ?= http://localhost:8080

VERSION           := 0.1.0
GIT_VERSION       ?= $(shell git rev-parse HEAD)
LDFLAGS           := -X github.com/jvassev/image2ipfs/util.Version=$(VERSION)/$(GIT_VERSION) -w -s

test:
	go test -v $(PKG)

install: test
	CGO_ENABLED=0 go install -v -ldflags "$(LDFLAGS)" $(PKG)

build-image: test
	CGO_ENABLED=0 docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE):$(TAG) --build-arg GIT_VERSION=$(GIT_VERSION) .

nested-build: test
	CGO_ENABLED=0 GOARCH=amd64 GOOS=linux go install -v -ldflags "$(LDFLAGS)" $(PKG)

shell:
	docker run --rm -ti -u root -v `pwd`:/workspace --entrypoint=/bin/sh $(IMAGE):$(TAG)

push-image: build-image
	docker push $(IMAGE):$(TAG)

guess-tag:
	@echo TAG=`git describe --match 'v[0-9]*' --dirty='.m' --always`

run-server: build-image
	docker run -ti --rm \
		--net=host \
		$(IMAGE):$(TAG)

clean:
	rm -fr dist

dist: clean test dist-linux dist-mac dist-win

dist-linux:
	@mkdir -p dist
	GOARCH=amd64 GOOS=linux CGO_ENABLED=0 go build -o dist/image2ipfs -v -ldflags "$(LDFLAGS)" $(PKG)
	gzip -S -$(VERSION)_amd64_linux.gz dist/image2ipfs

dist-mac:
	@mkdir -p dist
	GOARCH=amd64 GOOS=darwin CGO_ENABLED=0 go build -o dist/image2ipfs -v -ldflags "$(LDFLAGS)" $(PKG)
	gzip -S -$(VERSION)_amd64_darwin.gz dist/image2ipfs

dist-win:
	@mkdir -p dist
	GOARCH=amd64 GOOS=windows CGO_ENABLED=0 go build -o dist/image2ipfs.exe -v -ldflags "$(LDFLAGS)" $(PKG)
	gzip -cvf dist/image2ipfs.exe > dist/image2ipfs-$(VERSION)_amd64_windows.gz
	rm dist/image2ipfs.exe

