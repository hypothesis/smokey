# Hypothesis Smoke Tests

This repository contains smoke tests for the Hypothesis service and client.

## Configuration

The smoke tests are configured to run against `https://hypothes.is` by default.
The configuration can be overridden via environment variables.

See the `Makefile` for a list of recognized variables.

## Running the tests

Run the API end-to-end tests with:

```
make api-tests
```
