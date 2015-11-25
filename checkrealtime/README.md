checkrealtime: check that real-time annotation updates work
===========================================================

This is a small standalone [Go][go] program which tests that real-time
annotation updating is working in a deployed Hypothesis web service. It does
this in a rather crude but functional manner. It:

1. Connects to the websocket and asks to be streamed all annotation updates.
1. Creates an annotation using the API.
1. Waits for a short period to receive notification of the new annotation over
   the websocket.
1. Prints results (pass/fail) to STDOUT.

Currently, `checkrealtime` is installed and running as an Icinga check on
[the monitoring server](https://mon.hypothes.is/).

Usage
-----

Building `checkrealtime` requires:

1. a working [Go](https://golang.org/pkg/log/) toolchain with [GB][gb]
   [installed and working](http://getgb.io/docs/install/).
1. [Docker](https://www.docker.com/).

To build and run `checkrealtime`, simply run:

    make

The tool is built into a docker image in order to ensure isolation and to
simplify deployment (the resulting docker image can be deployed via Docker Hub).

You can also build `checkrealtime` locally, by running gb:

    gb build

You can then run the tool:

    ./bin/checkrealtime -h

You will need to supply a valid username and API token at a minimum for
`checkrealtime` to complete a check. For example:

    ./bin/checkrealtime -apiUser acct:foo@hypothes.is -apiToken eyJh...7HgQ

These parameters can also be supplied as environment variables. See the output
of `checkrealtime -h` for reference.

[go]: https://golang.org/
[gb]: http://getgb.io/
