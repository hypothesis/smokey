default: run

build:
	docker build -t hypothesis/smokey .

run: build
	# Use -t in order to get coloured output
	docker run -t hypothesis/smokey

.PHONY: default build run
