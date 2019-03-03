package main

import "testing"

func TestConvert(t *testing.T) {
	b32 := "ciqizic7pchyn7y7trnis24rp4y5jal4fixlytecaap2k4jawrdp6gi"

	b58, err := ipfsyDigest(b32)
	if err != nil {
		panic(err)
	}

	if "QmXobd2Bvr2NaLwvWamszFEZQVw9qMh5rJtdx9CSwQWw5a" != b58 {
		panic("bad conversion")
	}
}
