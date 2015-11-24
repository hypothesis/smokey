Hypothesis testing tools
========================

This repository contains tools used to test a running Hypothesis instance and
and documentation for operators.

`checkrealtime/`
----------------

A small program to check that "realtime annotation" (annotation updates streamed
down a websocket) is working correctly.


`smokey/`
---------

A smoke test suite powered by [behave][behave].


`misc/`
-------

This currently contains some fairly hairy ad-hoc scripts that have historically
been used to test the Hypothesis web service. Stuff in here is not currently
deployed as part of our monitoring or post-deploy testing infrastructure -- it's
here to serve as a reference as we build out better testing.

[behave]: https://pythonhosted.org/behave/
