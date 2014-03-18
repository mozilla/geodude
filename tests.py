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

import pygeoip
from mock import patch
from nose.tools import eq_, ok_
from webob import Request

import geodude

COUNTRY_DATA = {
    '0.0.0.0': {'country_code': 'us', 'country_name': 'United States'},
    '1.1.1.1': {'country_code': 'fr', 'country_name': 'France'},
}

MMDB_COUNTRY_DATA = {
    '0.0.0.0': {
        u'country': {
            u'geoname_id': 6252001,
            u'iso_code': u'US',
            u'names': {u'fr': u'\xc9tats-Unis', u'en': u'United States'}}
    },
    '1.1.1.1': {
        u'country': {
            u'geoname_id': 3017382,
            u'iso_code': u'FR',
            u'names': {u'fr': u'France', u'en': u'France'}}
    },
}

def fake_geo_data(ip):
    return COUNTRY_DATA[ip]


def request(path, allow_post=False, **kwargs):
    app = geodude.make_application(fake_geo_data, allow_post)
    request = Request.blank(path, **kwargs)
    return request.get_response(app)


def test_javascript_basic():
    response = request('/country.js', remote_addr='0.0.0.0')

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'text/javascript')
    ok_("function geoip_country_code() { return 'us'; }" in response.body)
    ok_("function geoip_country_name() { return 'United States'; }"
        in response.body)


def test_cluster_client_ip():
    response = request('/country.js',
                       headers={'X-Cluster-Client-IP': '0.0.0.0'})

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


def test_ip_post():
    response = request('country.json', allow_post=True,
                       remote_addr='0.0.0.0',
                       POST={'ip': '1.1.1.1'})

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'application/json')
    data = json.loads(response.body)
    eq_({'country_code': 'fr', 'country_name': 'France'}, data)


def test_post_without_ip():
    response = request('country.json', allow_post=True,
                       remote_addr='0.0.0.0', POST={})

    eq_(response.status, '400 Bad Request')
    eq_(response.content_type, 'application/json')
    data = json.loads(response.body)
    eq_({'error': '`ip` required in POST body.'}, data)


def test_ip_post_without_ALLOW_POST():
    response = request('country.json', allow_post=False,
                       remote_addr='0.0.0.0',
                       POST={'ip': '1.1.1.1'})

    eq_(response.status, '200 OK')
    eq_(response.content_type, 'application/json')
    data = json.loads(response.body)
    eq_({'country_code': 'us', 'country_name': 'United States'}, data)


def test_load_geoip():
    with patch('pygeoip.GeoIP') as fake_GeoIP:
        dbname = 'awesome_geoip.db'
        ip = '1.1.1.1'
        fetch = geodude.load_geoip(dbname)
        fake_GeoIP.assert_called_with(dbname, pygeoip.MEMORY_CACHE)

        ccba = fake_GeoIP.return_value.country_code_by_addr
        ccna = fake_GeoIP.return_value.country_name_by_addr
        ccba.return_value = 'fr'
        ccna.return_value = 'France'
        result = fetch(ip)
        eq_(result['country_code'], 'fr')
        eq_(result['country_name'], 'France')
        ccba.assert_called_with(ip)
        ccna.assert_called_with(ip)

def test_load_mmdb():
    with patch('maxminddb.Reader') as fake_Reader:
        dbname = 'awesome.mmdb'
        ip = '1.1.1.1'
        fetch = geodude.load_mmdb(dbname)
        fake_Reader.assert_called_with(dbname)
        fake_Reader().get.side_effect = MMDB_COUNTRY_DATA.get
        result = fetch(ip)
        eq_(result['country_code'], 'fr')
        eq_(result['country_name'], 'France')
