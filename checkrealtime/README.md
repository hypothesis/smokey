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

Developing
----------

You should ensure you have a working Go toolchain before attempting to work on
`checkrealtime`.

Vendor dependencies are managed by [GB][gb]. Ensure you have GB [installed and
working](http://getgb.io/docs/install/). Once you do, you should be able to
build `checkrealtime` by running the following from this directory:

    gb build

You should then be able to run `checkrealtime`:

    ./bin/checkrealtime -h

You will need to supply a valid username and API token at a minimum for
`checkrealtime` to complete a check. For example:

    ./bin/checkrealtime -apiUser acct:foo@hypothes.is -apiToken eyJh...7HgQ

These parameters can also be supplied as environment variables. See the output
of `checkrealtime -h` for reference.

[go]: https://golang.org/
[gb]: http://getgb.io/
