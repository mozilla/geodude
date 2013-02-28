import codecs
import os
import re
from setuptools import setup, find_packages


def read(*parts):
    return codecs.open(os.path.join(os.path.dirname(__file__), *parts)).read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='geodude',
    description=("Small WSGI geolocation service that identifies the user's "
                 "country based on their IP address."),
    long_description=read('README.md'),
    version=find_version('geodude.py'),
    packages=find_packages(),
    author='Michael Kelly',
    author_email='mkelly@mozilla.com',
    url='https://github.com/mozilla/geodude',
    license='Apache License v2.0',
    install_requires=['pygeoip', 'WebOb'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
)
