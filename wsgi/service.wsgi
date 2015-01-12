from os import environ

from geodude import load_geodude

try:
    import newrelic.agent
except ImportError:
    pass

application = load_geodude()

# Add NewRelic
newrelic_ini = environ.get('NEW_RELIC_CONFIG_FILE', 'newrelic.ini')
newrelic_license_key = environ.get('NEW_RELIC_LICENSE_KEY', None)
if newrelic_ini and newrelic_license_key:
    newrelic.agent.initialize(newrelic_ini)
    application = newrelic.agent.wsgi_application()(application)
