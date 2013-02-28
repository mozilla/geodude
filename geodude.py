#!/usr/bin/env python
import argparse
import inspect
import json
import os
from wsgiref.simple_server import make_server

import pygeoip
from webob import Request, Response


geoip = pygeoip.GeoIP(os.path.dirname(os.path.abspath(__file__))+'/GeoIP.dat', pygeoip.MEMORY_CACHE)


def application(environ, start_response):
    """
    Parse the request and geolocate the user via IP.

    :return:
        Response containing the user's country based on their IP address.
    """
    request = Request(environ)
    response = Response(
        status=200,
        cache_control=('no-store, no-cache, must-revalidate, post-check=0, '
                       'pre-check=0, max-age=0'),
        pragma='no-cache',
        expires='02 Jan 2010 00:00:00 GMT',
    )

    client_ip = request.headers.get('HTTP_X_CLUSTER_CLIENT_IP',
                                    request.client_addr)
    geo_data = {
        'country_code': geoip.country_code_by_addr(client_ip),
        'country_name': geoip.country_name_by_addr(client_ip),
    }

    # Users can request either a JavaScript file or a JSON file for the output.
    path = request.path_info_peek()
    if path == 'country.js':
        response.content_type = 'text/javascript'
        response.body = """
            function geoip_country_code() {{ return '{country_code}'; }}
            function geoip_country_name() {{ return '{country_name}'; }}
        """.format(**geo_data)
    elif path == 'country.json':
        response.content_type = 'application.json'
        response.body = json.dumps(geo_data)
    else:
        response.content_type = 'application.json'
        response.body = json.dumps({'error': 'Function not supported.'})

    return response(environ, start_response)


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
    server = make_server('', int(port), application)
    print 'Serving HTTP on port {0}...'.format(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Exiting server...'


@command
def test_ip(ip_address, path='/country.js'):
    """Run a mock request against the service."""
    request = Request.blank(path, remote_addr=ip_address)
    response = request.get_response(application)
    print response.status
    for header in response.headers:
        print header, ':', response.headers[header]
    print '\n', response.body


def main():
    """Parses command-line arguments and delegates to the specified command."""
    args = vars(parser.parse_args())
    func = args.pop('func')
    func(**args)

if __name__ == '__main__':
    main()
