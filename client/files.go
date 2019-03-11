package client

import (
	"archive/tar"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"io"
	"os"
	"path"
	"time"
)

func untar(f *os.File, dir string) error {
	tarBallReader := tar.NewReader(f)
	for {
		header, err := tarBallReader.Next()
		if err != nil {
			if err == io.EOF {
				break
			}
			return err
		}

		filename := header.Name
		fullPath := path.Join(dir, filename)

		switch header.Typeflag {
		case tar.TypeDir:
			// handle directory
			err = os.MkdirAll(fullPath, os.FileMode(header.Mode)) // or use 0755 if you prefer
			if err != nil {
				return err
			}

		case tar.TypeReg:
			// handle normal file
			writer, err := os.Create(fullPath)

			if err != nil {
				return err
			}

			_, err = io.Copy(writer, tarBallReader)
			if err != nil {
				return err
			}

			err = os.Chmod(fullPath, os.FileMode(header.Mode))
			if err != nil {
				return err
			}

			writer.Close()
		default:
			//fmt.Printf("Unable to untar type : %c in file %s", header.Typeflag, filename)
		}
	}

	return nil
}

func fileLength(name string) int64 {
	fi, err := os.Stat(name)
	if err != nil {
		return -1
	}

	return fi.Size()
}

func gzipFile(src string, dest string) (string, int64, error) {
	srcFile, err := os.Open(src)
	if err != nil {
		return "", 0, err
	}
	defer srcFile.Close()

	destFile, err := os.OpenFile(dest, os.O_CREATE|os.O_WRONLY, os.FileMode(0644))
	if err != nil {
		return "", 0, err
	}
	defer destFile.Close()

	digester := sha256.New()

	gz := gzip.NewWriter(destFile)
	gz.ModTime = time.Unix(0, 0)

	tee := io.MultiWriter(gz, digester)

	_, err = io.Copy(tee, srcFile)
	if err != nil {
		return "", 0, err
	}

	gz.Flush()
	gz.Close()
	return hex.EncodeToString(digester.Sum(nil)), fileLength(dest), nil
}
