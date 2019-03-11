package util

import "testing"

func TestConvert(t *testing.T) {
	b32 := "ciqizic7pchyn7y7trnis24rp4y5jal4fixlytecaap2k4jawrdp6gi"
	b58 := "QmXobd2Bvr2NaLwvWamszFEZQVw9qMh5rJtdx9CSwQWw5a"

	ipfs, err := IpfsyDigest(b32)
	if err != nil {
		panic(err)
	}

	if ipfs != b58 {
		panic("bad conversion to ipfs")
	}

	docker, _ := DockerizeDigest(b58)
	if docker != b32 {
		panic("bad conversion to docker:" + docker)
	}
}
