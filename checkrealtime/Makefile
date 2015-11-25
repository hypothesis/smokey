default: run

bin/checkrealtime-linux-amd64:
	GOOS=linux GOARCH=amd64 gb build

build: bin/checkrealtime-linux-amd64
	docker build -t hypothesis/checkrealtime .

run: build
	docker run hypothesis/checkrealtime

clean:
	rm -rf pkg/ bin/

.PHONY: default build run clean
