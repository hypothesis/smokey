# The statically linked Go binary makes it possible to build a minimalist Docker
# image: 'scratch' is the virtual null image, with no layers.
FROM scratch
COPY bin/checkrealtime-linux-amd64 /checkrealtime
ENTRYPOINT ["/checkrealtime"]
