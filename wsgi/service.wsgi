from os import environ

from geodude import load_geodude

try:
    import newrelic.agent
except ImportError:
    pass

application = load_geodude()

# Add NewRelic
newrelic_ini = environ.get('NEWRELIC_PYTHON_INI_FILE', False)
if newrelic_ini:
    newrelic.agent.initialize(newrelic_ini)
    application = newrelic.agent.wsgi_application()(application)
