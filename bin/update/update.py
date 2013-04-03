import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import BadReturnCode, hostgroups, task

import commander_settings as settings


_src_dir = lambda *p: os.path.join(settings.SRC_DIR, *p)
VIRTUALENV = os.path.join(os.path.dirname(settings.SRC_DIR), 'venv')


@task
def create_virtualenv(ctx):
    venv = VIRTUALENV
    if not venv.startswith('/data'):
        raise Exception('venv must start with /data')  # this is just to avoid rm'ing /

    ctx.local('rm -rf %s' % venv)
    ctx.local('virtualenv --distribute --never-download %s' % venv)

    ctx.local('%s/bin/pip install --exists-action=w --no-deps --no-index '
              '--download-cache=/tmp/pip-cache -f %s '
              '-r %s/requirements/prod.txt' %
              (venv, settings.PYREPO, settings.SRC_DIR))

    # make sure this always runs
    ctx.local("rm -f %s/lib/python2.6/no-global-site-packages.txt" % venv)
    ctx.local("%s/bin/python /usr/bin/virtualenv --relocatable %s" % (venv, venv))


@task
def update_code(ctx, ref='origin/master'):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git fetch && git fetch -t")
        ctx.local("git reset --hard %s" % ref)


@task
def update_info(ctx, ref='origin/master'):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git status")
        ctx.local("git log -1")
        ctx.local("/bin/bash -c 'source /etc/bash_completion.d/git && __git_ps1'")


@task
def checkin_changes(ctx):
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def sync_code(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def restart_workers(ctx):
    if getattr(settings, 'GUNICORN', False):
        for gservice in settings.GUNICORN:
            ctx.remote("/sbin/service %s graceful" % gservice)
    else:
        ctx.remote("/bin/touch %s/geodude.py" % settings.REMOTE_APP)


@task
def deploy_app(ctx):
    sync_code()
    restart_workers()


@task
def deploy(ctx):
    checkin_changes()
    deploy_app()


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    ctx.local('date')
    update_code(ref)
    update_info(ref)


@task
def update(ctx):
    create_virtualenv()
