import os
from fabric.api import (env, execute, lcd, local, parallel,
                        run, roles, task)

from fabdeploytools import helpers
import fabdeploytools.envs

import deploysettings as settings


env.key_filename = settings.SSH_KEY
fabdeploytools.envs.loadenv(settings.CLUSTER)

ROOT, GEODUDE = helpers.get_app_dirs(__file__)

VIRTUALENV = os.path.join(ROOT, 'venv')
PYTHON = os.path.join(VIRTUALENV, 'bin', 'python')
GEOIP_DB = '/usr/share/GeoIP/GeoIP2-City.mmdb'


def managecmd(cmd):
    with lcd(GEODUDE):
        local('%s manage.py %s' % (PYTHON, cmd))


@task
def create_virtualenv():
    helpers.create_venv(VIRTUALENV, settings.PYREPO,
                        '%s/requirements/prod.txt' % GEODUDE,
                        update_on_change=True, rm_first=True)


@task
def update_info(ref='origin/master'):
    helpers.git_info(GEODUDE)
    with lcd(GEODUDE):
        local("/bin/bash -c "
              "'source /etc/bash_completion.d/git && __git_ps1'")
        local('git show -s {0} --pretty="format:%h" '
              '> media/git-rev.txt'.format(ref))


@task
def sync_geoipdb():
    local('cp {0} {1}'.format(GEOIP_DB, GEODUDE))


@task
def deploy():
    helpers.deploy(name='geodude',
                   env=settings.ENV,
                   cluster=settings.CLUSTER,
                   domain=settings.DOMAIN,
                   root=ROOT,
                   package_dirs=['geodude', 'venv'])

    helpers.restart_uwsgi(getattr(settings, 'UWSGI', []))


@task
def pre_update(ref=settings.UPDATE_REF):
    local('date')
    execute(helpers.git_update, GEODUDE, ref)
    execute(update_info, ref)


@task
def update():
    execute(create_virtualenv)


@task
def build():
    execute(create_virtualenv)
    execute(sync_geoipdb)


@task
def deploy_jenkins():
    rpm = helpers.build_rpm(name='geodude',
                            env=settings.ENV,
                            cluster=settings.CLUSTER,
                            domain=settings.DOMAIN,
                            package_dirs=['geodude', 'venv'],
                            root=ROOT)

    rpm.local_install()
    rpm.remote_install(['web'])
    helpers.restart_uwsgi(getattr(settings, 'UWSGI', []))
