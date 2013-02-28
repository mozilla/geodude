#!/usr/bin/env python
import argparse
import gzip
import inspect
import sys
from urllib import urlretrieve
from wsgiref.simple_server import make_server

import nose
from webob import Request


parser = argparse.ArgumentParser(description=globals()['__doc__'],
                                 formatter_class=argparse.RawTextHelpFormatter)
subparsers = parser.add_subparsers(title='Commands')


def command(func):
    """
    Decorator that turns a function into a sub-command.

    The command will be named after the function, and the help text will be
    taken from the docstring. Command arguments are automatically set up based
    on the function arguments.
    """
    cmd_parser = subparsers.add_parser(func.__name__, help=func.__doc__)
    cmd_parser.set_defaults(func=func)  # Set which function this command runs.

    # Inspect the function arguments and create them on the parser.
    spec = inspect.getargspec(func)
    for idx, arg in enumerate(spec.args):
        try:
            # First try treating this is a kwarg.
            default_index = idx - (len(spec.args) - len(spec.defaults))
            cmd_parser.add_argument(arg, default=spec.defaults[default_index],
                                    nargs='?')
        except (TypeError, IndexError):
            # Required, positional argument.
            cmd_parser.add_argument(arg)

    return func


@command
def runserver(port=8000):
    """Run a development instance of the geodude server."""
    from geodude import application

    server = make_server('', int(port), application)
    print 'Serving HTTP on port {0}...'.format(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Exiting server...'


@command
def test_ip(ip_address, path='/country.js'):
    """Run a mock request against the service."""
    from geodude import application

    request = Request.blank(path, remote_addr=ip_address)
    response = request.get_response(application)
    print response.status
    for header in response.headers:
        print header, ':', response.headers[header]
    print '\n', response.body


@command
def download_db():
    """Download MaxMind's free GeoLite Country database."""
    urlretrieve('http://geolite.maxmind.com/download/geoip/database/'
                'GeoLiteCountry/GeoIP.dat.gz', 'GeoIP.dat.gz')
    with gzip.open('GeoIP.dat.gz') as infile:
        with open('GeoIP.dat', 'w+b') as outfile:
            outfile.write(infile.read())


@command
def test():
    """Run the test suite."""
    argv = sys.argv
    argv.pop(1)
    nose.main(argv=argv)


def main():
    """Parses command-line arguments and delegates to the specified command."""
    args = vars(parser.parse_args())
    func = args.pop('func')
    func(**args)

if __name__ == '__main__':
    main()
