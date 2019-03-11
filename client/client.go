package client

import (
	"io/ioutil"
	"log"
	"os"

	"golang.org/x/crypto/ssh/terminal"
	"gopkg.in/alecthomas/kingpin.v2"
)

var clientCmd = kingpin.Command("client", "Populate IPFS node with image data").Default()

var registry = clientCmd.Flag("registry", "Registry to use when generating pull URL").
	Short('r').
	Default("http://localhost:5000").
	String()

var noAdd = clientCmd.Flag("no-add", "Don`t add to IPFS, just print directory").
	Short('n').
	Bool()

var quiet = clientCmd.Flag("quiet", "Produce less output - just the final pullable image name").
	Short('q').
	Bool()

var debug = clientCmd.Flag("debug", "Leave workdir intact (useful for debugging)").
	Short('d').
	Bool()

var input = clientCmd.Flag("input", "Docker image archive to process, defaults to stdin. Use - to explicitly set stdin").
	Short('i').
	Default("-").
	String()

func Run() {
	w := Work{}

	if *input == "-" {
		if terminal.IsTerminal(int(os.Stdin.Fd())) {
			log.Fatalf("input is terminal")
		}
		w.Input = os.Stdin
	} else {
		f, err := os.Open(*input)
		if err != nil {
			log.Fatalf("cannot open %s: %+v", *input, err)
		}
		w.Input = f
		defer f.Close()
	}

	d, err := ioutil.TempDir("", "image2ipfs")
	if err != nil {
		log.Fatalf("cannot create temp dir: %+v", err)
	}

	if *quiet {
		log.SetOutput(ioutil.Discard)
	}

	log.Printf("workdir is %s", d)
	w.Dir = d
	// TODO delete tmp dir
	w.Process()
}
