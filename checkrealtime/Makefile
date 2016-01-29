GOHOSTOS := $(shell go env GOHOSTOS)
GOHOSTARCH := $(shell go env GOHOSTARCH)
GOTARGETSUFFIX := -linux-amd64

default: run

bin/checkrealtime$(GOTARGETSUFFIX):
	GOOS=linux GOARCH=amd64 gb build

bin/checkrealtime-docker: bin/checkrealtime$(GOTARGETSUFFIX)
	cp $< $@

build: bin/checkrealtime-docker
	docker build -t hypothesis/checkrealtime .

run: build
	docker run hypothesis/checkrealtime

clean:
	rm -rf pkg/ bin/

.PHONY: default build run clean
