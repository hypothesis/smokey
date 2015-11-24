# Smokey, a smoke test suite

This directory contains tools to run a test suite which is designed primarily to
ensure the correct functioning of a deployed Hypothesis web service, either as a
post-deploy check or as part of a periodic monitoring solution.

## Usage

To run the tests, simply run:

    make

The test suite is built into a docker image in order to ensure isolation (the
result of the tests is not affected by the state of the machine running the
tests) and reproducibility (if the service remains in the same state, the tests
return the same result each time).

You can build the docker image by hand with a command such as

    docker build -t hypothesis/smokey .

The resulting image (`hypothesis/smokey`) can then be run with:

    docker run hypothesis/smokey

## Configuration

By default the tests will run against the production web service at
`https://hypothes.is`. You can configure a different base URL using an
environment variable:

    docker run -e API_ENDPOINT='https://myserver/api' hypothesis/smokey
