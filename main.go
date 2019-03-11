package main

import (
	"github.com/jvassev/image2ipfs/client"
	"github.com/jvassev/image2ipfs/server"
	"github.com/jvassev/image2ipfs/util"
	"gopkg.in/alecthomas/kingpin.v2"
)

func main() {
	kingpin.Version(util.Version)

	switch kingpin.Parse() {
	case "server":
		server.Run()
	case "client":
		client.Run()
	}
}
