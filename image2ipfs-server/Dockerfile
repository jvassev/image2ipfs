FROM golang:1.10 as builder

WORKDIR /go/src/github.com/jvassev/image2ipfs
COPY . .
RUN make install-server

# Speed up local builds where vendor is populated
FROM busybox
ENTRYPOINT ["image2ipfs-server"]
COPY --from=builder /go/bin/image2ipfs-server /bin
