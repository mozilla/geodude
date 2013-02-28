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
