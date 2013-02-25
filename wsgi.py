import glob, os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/lib/pygeoip')
import pygeoip
from webob import Request
from cgi import parse_qs

def application(environ, start_response):
    if "Firefox" in environ["HTTP_USER_AGENT"]:
        content = 'text/plain'
    else:
        content = 'application/json'

    start_response('200 OK',
    [('Content-type', content ),
    ('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'),
    ('Pragma', 'no-cache'),
    ('Expires', '02 Jan 2010 00:00:00 GMT' )])

    try:
        client_ip = environ['HTTP_X_CLUSTER_CLIENT_IP']
    except KeyError:
        client_ip = environ['REMOTE_ADDR']

    gi = pygeoip.GeoIP(os.path.dirname(os.path.abspath(__file__))+'/GeoIP.dat', pygeoip.MEMORY_CACHE)
    country_code = gi.country_code_by_addr(client_ip)
    country_name = gi.country_name_by_addr(client_ip)

    if Request(environ).path_info_peek() == 'country.js':
        yield "function geoip_country_code() { return '%s'; }\n" % country_code
        yield "function geoip_country_name() { return '%s'; }\n" % country_name
        return

    yield '{"error": "Function not supported."}'
