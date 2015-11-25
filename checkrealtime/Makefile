GOHOSTOS := $(shell go env GOHOSTOS)
GOHOSTARCH := $(shell go env GOHOSTARCH)

# If we're building on an OS or architecture other than linux-amd64, the target
# will be created with the -linux-amd64 suffix, so we need to account for that.
GOTARGETSUFFIX :=
ifneq ($(GOHOSTOS)-$(GOHOSTARCH),linux-amd64)
	GOTARGETSUFFIX := -linux-amd64
endif

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
