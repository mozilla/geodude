#!/bin/sh
# This script makes sure that Jenkins can properly run your tests against your
# codebase.
set -e

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build on executor $EXECUTOR_NUMBER..."

# Make sure there's no old pyc files around.
find . -name '*.pyc' -exec rm {} \;

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV --no-site-packages
  source $VENV/bin/activate
  pip install --upgrade pip
  pip install coverage
fi

source $VENV/bin/activate
pip install -q -r requirements/dev.txt

cat > settings.py <<SETTINGS
import os


ROOT = os.path.abspath(os.path.dirname(__file__))
def path(*a):
    return os.path.join(ROOT, *a)


# Set to True if this is a local development instance.
DEV = False

# Absolute path to the geoip binary data file.
GEO_DB_PATH = path('GeoIP.dat')
SETTINGS

echo "Download GeoIP database..."
./geodude.py install_db


echo "Starting tests..."
coverage run manage.py test
coverage xml $(find apps lib -name '*.py')

echo "FIN"
