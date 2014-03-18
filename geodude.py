# Copyright 2013 The Mozilla Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import os
import sys

from webob import Request, Response

import pygeoip
import maxminddb

__version__ = '0.2'

def load_geoip(db_path):
    geoip = pygeoip.GeoIP(db_path, pygeoip.MEMORY_CACHE)
    def fetch_geo_data(ip):
        return {
            'country_code': geoip.country_code_by_addr(ip),
            'country_name': geoip.country_name_by_addr(ip),
        }
    return fetch_geo_data


def load_mmdb(db_path):
    reader = maxminddb.Reader(db_path)
    def fetch_geo_data(ip):
        data = reader.get(ip)
        return {
            'country_code': data['country']['iso_code'].lower(),
            'country_name': data['country']['names']['en'],
        }
    return fetch_geo_data


def make_application(fetch_geo_data, allow_post=False):
    def application(environ, start_response):
        """Determine the user's country based on their IP address."""
        request = Request(environ)
        response = Response(
            status=200,
            cache_control=('no-store, no-cache, must-revalidate, post-check=0, '
                           'pre-check=0, max-age=0'),
            pragma='no-cache',
            expires='02 Jan 2010 00:00:00 GMT',
        )

        if allow_post and request.method == 'POST':
            if 'ip' in request.POST:
                client_ip = request.POST['ip']
            else:
                response = error(response, 400, '`ip` required in POST body.')
                return response(environ, start_response)
        else:
            client_ip = request.headers.get('X-Cluster-Client-IP',
                                            request.client_addr)
        geo_data = fetch_geo_data(client_ip)

        # Users can request either a JavaScript file or a JSON file for the output.
        path = request.path_info_peek()
        if path == 'country.js':
            response.content_type = 'text/javascript'
            response.body = """
                function geoip_country_code() {{ return '{country_code}'; }}
                function geoip_country_name() {{ return '{country_name}'; }}
            """.format(**geo_data)
        elif path == 'country.json':
            response.content_type = 'application/json'
            response.body = json.dumps(geo_data)
        else:
            response = error(response, 404, 'Function not supported.')

        return response(environ, start_response)
    return application

def error(response, code, message):
    response.status = code
    response.content_type = 'application/json'
    response.body = json.dumps({'error': message})
    return response


def load_geodude():
    # Add current directory to path so we can import settings.
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    import settings
    fmt = getattr(settings, 'GEO_DB_FORMAT', 'geoip')
    if fmt == 'geoip':
        load = load_geoip
    else:
        load = load_mmdb

    return make_application(
        load(settings.GEO_DB_PATH),
        settings.ALLOW_POST)
