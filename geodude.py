import json
import os

import pygeoip
from webob import Request, Response


geoip = pygeoip.GeoIP(os.path.dirname(os.path.abspath(__file__)) + '/GeoIP.dat', pygeoip.MEMORY_CACHE)


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
