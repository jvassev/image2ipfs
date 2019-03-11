package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path"
	"strings"

	"github.com/jvassev/image2ipfs/util"
)

type Work struct {
	Input *os.File
	Dir   string

	Name string
}

func simplifyName(name string) string {
	//"""Remove host/port part from an image name"""
	i := strings.LastIndex(name, "/")
	if i < 0 {
		return name
	}
	maybe_url := name[:i]
	if strings.Index(maybe_url, ".") >= 0 || strings.Index(maybe_url, ":") >= 0 {
		return name[i+1:]
	}

	return name
}

func (w *Work) Process() {
	err := untar(w.Input, w.Dir)
	if err != nil {
		log.Fatalf("cannot extract tar file: %+v", err)
	}

	repos, err := w.jsonObj("repositories")
	if len(repos) != 1 {
		log.Fatalf("one repository expected, found %d", len(repos))
	}

	for name, obj := range repos {
		m := obj.(map[string]interface{})
		if len(m) != 1 {
			log.Fatalf("one image expected for the single repository %s, found %d", name, len(repos))
		} else {
			for tag := range m {
				w.Name = simplifyName(name)
				log.Printf("processing %s:%s", name, tag)
			}
		}
	}

	for _, p := range []string{"work/" + w.Name + "/manifests", "work/" + w.Name + "/blobs"} {
		err = os.MkdirAll(path.Join(w.Dir, p), os.FileMode(0755))
		if err != nil {
			log.Fatalf("cannot create folder %s in work dir", p)
		}
	}

	mf, err := w.jsonArray("manifest.json")
	if err != nil {
		log.Fatalf("cannot parse manifest: %s", err)
	}
	config := mf[0].(map[string]interface{})
	rootLayer := config["Config"].(string)

	layers := []string{}
	for _, obj := range config["Layers"].([]interface{}) {
		layers = append(layers, obj.(string))
	}

	rootLayerSha := rootLayer[0 : len(rootLayer)-5]
	configDest := path.Join(w.Dir, "work/"+w.Name+"/blobs", "sha256:"+rootLayerSha)
	err = os.Rename(path.Join(w.Dir, rootLayer), configDest)
	if err != nil {
		log.Fatalf("cannot create manifest in destination: %s", err)
	}

	manifest := &Manifest{
		SchemaVersion: ManifestVersion,
		MediaType:     ManifestType,
		Config: &Config{
			MediaType: ConfigType,
			Digest:    "sha256:" + rootLayerSha,
			Size:      fileLength(configDest),
		},
	}

	err = w.addLayers(manifest, layers)
	if err != nil {
		log.Fatalf("cannot compress layers: %s", err)
	}

	err = w.writeJSON("work/"+w.Name+"/manifests/latest-v2", manifest)
	if err != nil {
		log.Fatalf("cannot write final manifest: %s", err)
	}

	if *noAdd {
		log.Printf("NOT adding to IPFS")
		return
	}

	pullURL, err := w.addToIPFS()
	if err != nil {
		log.Fatalf("cannot write to IPFS. check if gateway is running and ipfs is on your path: %s", err)
	}

	if !*debug {
		err := os.RemoveAll(w.Dir)
		if err != nil {
			log.Printf("warning: cannot cleanup workdir: %s", err)
		}
	}

	fmt.Printf("%s\n", pullURL)
}

func (w *Work) addToIPFS() (string, error) {
	exe, err := exec.LookPath("ipfs")
	if err != nil {
		return "", fmt.Errorf("ipfs not found in your PATH")
	}

	log.Printf("using ipfs in %s", exe)

	cmd := exec.Command("ipfs", "add", "-r", "-Q", path.Join(w.Dir, "work"))

	var out bytes.Buffer
	cmd.Stdout = &out

	err = cmd.Run()
	if err != nil {
		return "", err
	}

	b, _ := ioutil.ReadAll(&out)
	h := strings.TrimSpace(string(b))

	log.Printf("image ready %s", h)
	log.Printf("browse image at http://localhost:8080/ipfs/%s", h)

	d, _ := util.DockerizeDigest(h)
	log.Printf("dockerized hash %s", d)

	pull := normalizeRegistry() + d + "/" + w.Name
	log.Printf("you can pull using %s", pull)

	return pull, nil
}

func normalizeRegistry() string {
	res := *registry

	i := strings.Index(res, "//")
	if i >= 0 {
		res = res[i+2:]
	}

	if res[len(res)-1] != '/' {
		res += "/"
	}

	return res
}

func (w *Work) addLayers(manifest *Manifest, layers []string) error {
	for _, layer := range layers {
		log.Printf("processing layer %s", path.Join(w.Dir, layer))
		newLayer := &Layer{
			MediaType: LayerType,
		}

		//err := w.copyLayer(newLayer, layer)
		err := w.compressLayer(newLayer, layer)
		if err != nil {
			return err
		}

		manifest.Layers = append(manifest.Layers, newLayer)
	}

	return nil
}

func (w *Work) compressLayer(layer *Layer, layerFile string) error {
	tmp := path.Join(w.Dir, layerFile+".tmp")

	sha, size, err := gzipFile(path.Join(w.Dir, layerFile), tmp)
	if err != nil {
		return err
	}

	dest := path.Join(w.Dir, "work/"+w.Name+"/blobs", "sha256:"+sha)
	err = os.Rename(tmp, dest)
	if err != nil {
		return err
	}

	layer.Size = size
	layer.Digest = "sha256:" + sha

	return nil
}

func (w *Work) copyLayer(layer *Layer, layerFile string) error {
	i := strings.Index(layerFile, "/")
	digest := layerFile[:i]

	dest := path.Join(w.Dir, "work/"+w.Name+"/blobs", "sha256:"+digest)
	err := os.Rename(path.Join(w.Dir, layerFile), dest)
	if err != nil {
		return err
	}

	layer.Digest = "sha256:" + digest
	layer.Size = fileLength(dest)

	return nil
}

func (w *Work) jsonObj(name string) (map[string]interface{}, error) {
	fullPath := path.Join(w.Dir, name)
	r, err := os.Open(fullPath)
	if err != nil {
		return nil, err
	}

	res := map[string]interface{}{}
	err = json.NewDecoder(r).Decode(&res)
	if err != nil {
		return nil, err
	}

	return res, nil
}

func (w *Work) writeJSON(name string, obj interface{}) error {
	f, err := os.OpenFile(path.Join(w.Dir, name), os.O_CREATE|os.O_WRONLY, os.FileMode(0755))
	if err != nil {
		return err
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	return enc.Encode(obj)
}

func (w *Work) jsonArray(name string) ([]interface{}, error) {
	fullPath := path.Join(w.Dir, name)
	r, err := os.Open(fullPath)
	if err != nil {
		return nil, err
	}

	res := []interface{}{}
	err = json.NewDecoder(r).Decode(&res)
	if err != nil {
		return nil, err
	}

	return res, nil
}
