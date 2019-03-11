package util

import (
	"encoding/base32"
	"strings"

	"github.com/btcsuite/btcutil/base58"
)

var b32Enc = base32.StdEncoding

func init() {
	b32Enc = b32Enc.WithPadding(base32.NoPadding)
}

func IpfsyDigest(digest string) (string, error) {
	bytes, err := b32Enc.DecodeString(strings.ToUpper(digest))
	if err != nil {
		return "", err
	}
	return string(base58.Encode(bytes)), nil
}

func DockerizeDigest(digest string) (string, error) {
	bytes := base58.Decode(digest)

	return strings.ToLower(b32Enc.EncodeToString(bytes)), nil
}
