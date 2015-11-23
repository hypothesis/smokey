# Via Service Tester

An end-to-end testing tool for the Via service.

It reads a configuration file specifying a set
of browsers to test with and a set of URLs
to test in each browser and loads the
specified URLs in each browser.

After loading each URL it performs
basic checks such as testing whether the
sidebar loads.

## Usage

```
export SAUCE_USERNAME=<username>
export SAUCE_ACCESS_KEY=<access key>
test-via.py -c <config.yml file>
```

## Configuration

The tester reads its configuration from a YAML file.
See `config.yml` for a reference of supported keys.

For tests using Sauce Labs browsers, the Sauce Labs
username and access key need to be specified via
`SAUCE_USERNAME` and `SAUCE_ACCESS_KEY` env vars.
