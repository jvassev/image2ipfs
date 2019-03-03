package main

import (
	"encoding/base32"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/btcsuite/btcutil/base58"
	"github.com/gorilla/mux"
	"gopkg.in/alecthomas/kingpin.v2"
)

const MF_SCHEMA_V2 = "application/vnd.docker.distribution.manifest.v2+json"

var gw = kingpin.Flag("gateway", "IPFS gateway. It must be reachable by pulling clients").
	Envar("IPFS_GATEWAY").
	Default("http://127.0.0.1:8080").
	String()

var addr = kingpin.Flag("addr", "Listen address. ").
	Default(":5000").
	String()

func main() {
	kingpin.Parse()
	log.Printf("Using IPFS gateway %s", *gw)
	r := mux.NewRouter()
	r.HandleFunc("/v2", info)
	r.HandleFunc("/v2/", info)
	r.NotFoundHandler = http.HandlerFunc(notFound)

	r.HandleFunc("/v2/{digest}/{path:.*}", blob)
	srv := &http.Server{
		Handler:      r,
		Addr:         *addr,
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	log.Printf("Serving on %s", *addr)
	log.Fatal(srv.ListenAndServe())
}

func notFound(w http.ResponseWriter, r *http.Request) {
	log.Printf("not found %s", r.URL)
}

func info(w http.ResponseWriter, r *http.Request) {
	info := map[string]interface{}{}
	info["what"] = "A docker registry that will redirect to an IPFS gateway"
	info["gateway"] = *gw
	info["project"] = "https://github.com/jvassev/image2ipfs"

	js, err := json.Marshal(info)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Docker-Distribution-API-Version", "registry/2.0")
	w.WriteHeader(http.StatusOK)
	w.Write(js)
}

func ipfsyDigest(digest string) (string, error) {
	bytes, err := base32.StdEncoding.DecodeString(strings.ToUpper(digest) + "=")
	if err != nil {
		return "", err
	}
	return string(base58.Encode(bytes)), nil
}

func blob(w http.ResponseWriter, r *http.Request) {
	//log.Printf("%s (%s)", r.URL, r.Header["Accept"])

	// @app.route('/v2/<string:digest>/<path:path>')
	vars := mux.Vars(r)
	digest := vars["digest"]
	path := vars["path"]

	isManifest := false
	for _, a := range r.Header["Accept"] {
		if a == MF_SCHEMA_V2 {
			isManifest = true
			break
		}
	}

	h, err := ipfsyDigest(digest)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	if isManifest {
		// do forward instead of proxying just to set the content-type
		location := *gw + "/ipfs/" + h + "/" + path + "-v2"
		log.Printf("Get the manifest of %s from %s", r.URL, location)
		response, err := http.Get(location)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-type", MF_SCHEMA_V2)
		w.WriteHeader(response.StatusCode)
		io.Copy(w, response.Body)
	} else {
		location := *gw + "/ipfs/" + h + "/" + path
		if strings.HasSuffix(path, "/latest") {
			location += "-v2"
		}

		log.Printf("Redirecting blob of %s to %s", r.URL, location)
		w.Header().Set("Location", location)
		w.WriteHeader(http.StatusPermanentRedirect)
	}
}
