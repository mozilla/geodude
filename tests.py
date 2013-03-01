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

from mock import patch
from nose.tools import eq_, ok_
from webob import Request

from geodude import application


def request(path, country_data=None, **kwargs):
    if country_data is None:
        country_data = {
            '0.0.0.0': {'code': 'us', 'name': 'United States'},
            '1.1.1.1': {'code': 'fr', 'name': 'France'},
        }

    with patch('geodude.geoip') as geoip:
        def country_code_by_addr(ip):
            return country_data[ip]['code']
        geoip.country_code_by_addr.side_effect = country_code_by_addr

        def country_name_by_addr(ip):
            return country_data[ip]['name']
        geoip.country_name_by_addr.side_effect = country_name_by_addr

        request = Request.blank(path, **kwargs)
        return request.get_response(application)


def test_javascript_basic():
    response = request('/country.js', remote_addr='0.0.0.0')

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'text/javascript')
    ok_("function geoip_country_code() { return 'us'; }" in response.body)
    ok_("function geoip_country_name() { return 'United States'; }"
        in response.body)


def test_cluster_client_ip():
    response = request('/country.js',
                       headers={'HTTP_X_CLUSTER_CLIENT_IP': '0.0.0.0'})

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'text/javascript')
    ok_("function geoip_country_code() { return 'us'; }" in response.body)
    ok_("function geoip_country_name() { return 'United States'; }"
        in response.body)


def test_json():
    response = request('/country.json', remote_addr='1.1.1.1')

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'application/json')
    data = json.loads(response.body)
    eq_({'country_code': 'fr', 'country_name': 'France'}, data)


def test_invalid_path():
    response = request('/invalid.html', remote_addr='1.1.1.1')

    eq_(response.status, '404 Not Found')
    eq_(response.content_type, 'application/json')
    data = json.loads(response.body)
    eq_({'error': 'Function not supported.'}, data)
