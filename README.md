# geodude

WSGI application that uses geolocation to determine visitors' countries based on
their IP address.


## Configuration

Geodude supports either the GeoIP database format or Maxmind's MMDB
format. Indicate which to use by setting `GEO_DB_FORMAT` in
settings.py to either `'geoip'` or `'mmdb'`.

## Endpoints

Endpoints only return the visitors location unless you turn on `ALLOW_POST` in
the settings. When that setting is enabled you can POST to the following
endpoints with this body:

```
ip=0.0.0.0
```

### /country.js

```javascript
function geoip_country_code() { return 'US'; }
function geoip_country_name() { return 'United States'; }
```

### /country.json

```json
{"country_name": "United States", "country_code": "US"}
```

### Anything else

```json
{"error": "Function not supported."}
```


## Developer Setup

1. Clone the repo: `git clone git://github.com/mozilla/geodude.git`

2. **Recommended:** Create a [virtualenv][] and activate it.

3. Install development dependencies using `pip`:
   `pip install -r requirements/dev.txt`

4. Download the free [MaxMind GeoLite Country database][geolite] using the
   `download_db` command: `./manage.py download_db`

5. Copy the `settings.py-dist` file to `settings.py`:
   `cp settings.py-dist settings.py`

   The default values in this settings file should be fine for local
   development.


## `manage.py` Commands

### runserver

**Usage:** `./manage.py runserver [port=8000]`

Starts the development server. Optionally takes a port to run on; the default is
port 8000. Not all that useful, as all local requests will use `127.0.0.1` as
the IP address.

### test_ip

**Usage:** `./manage.py test_ip ip_address`

Runs a mock request against the application, using the given IP address as the
remote address. Useful for local testing.

### download_db

**Usage:** `./manage.py download_db`

Downloads the free [MaxMind GeoLite Country database][geolite] and unzips it in
the current directory to `GeoIP.dat`.

### test

**Usage:** `./manage.py test`

Runs the test suite.


## License

geodude is released under the [Apache License, Version 2.0][apache-license]. See
the `LICENSE` file for more info.


[virtualenv]: http://www.virtualenv.org
[geolite]: http://dev.maxmind.com/geoip/geolite
[apache-license]: http://www.apache.org/licenses/LICENSE-2.0
