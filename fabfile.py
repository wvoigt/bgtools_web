# Credit goes to https://bitbucket.org/spookylukey/django-fabfile-starter/src

import posixpath
from fabric.api import env, run, cd, task, local
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
from fabric.context_managers import settings
import psutil

from fabsettings import (USER, HOST, DJANGO_APP_NAME,  # noqa: F401
                         DJANGO_APPS_DIR, LOGS_ROOT_DIR,
                         APP_PORT, GUNICORN_WORKERS, DJANGO_PROJECT_NAME)

env.hosts = ['{}@{}'.format(USER, HOST)]
env.use_ssh_config = True

DJANGO_APP_ROOT = posixpath.join(DJANGO_APPS_DIR, DJANGO_PROJECT_NAME)

# Subdirectory of DJANGO_APP_ROOT in which virtualenv will be stored
VENV_SUBDIR = 'venv'

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = posixpath.join(PYTHON_PREFIX, 'bin', PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

GUNICORN_PIDFILE = posixpath.join(DJANGO_APP_ROOT, 'gunicorn.pid')
GUNICORN_LOGFILE = posixpath.join(LOGS_ROOT_DIR, 'gunicorn_{}.log'.format(DJANGO_PROJECT_NAME))

SRC_DIR = posixpath.join(DJANGO_APP_ROOT, DJANGO_PROJECT_NAME)
VENV_DIR = posixpath.join(DJANGO_APP_ROOT, VENV_SUBDIR)
CHECKOUT_DIR = posixpath.join(DJANGO_APP_ROOT, 'checkouts')

WSGI_MODULE = '{}.wsgi'.format(DJANGO_PROJECT_NAME)


def virtualenv(venv_dir):
    """
    Context manager that establishes a virtualenv to use.
    """
    return settings(venv=venv_dir)


def run_venv(command, **kwargs):
    """
    Runs a command in a virtualenv (which has been specified using
    the virtualenv context manager
    """
    run("source {}/bin/activate && {}".format(env.venv, command), **kwargs)


@task
def install_dependencies():
    ensure_virtualenv()
    rsync_source()
    with virtualenv(VENV_DIR):
        with cd(SRC_DIR):
            run_venv("pip install -r requirements.txt")


def ensure_virtualenv():
    ensure_dir(SRC_DIR)
    if exists(VENV_DIR):
        return

    with cd(DJANGO_APP_ROOT):
        run("virtualenv --no-site-packages --python={} {}".format(
            PYTHON_BIN, VENV_SUBDIR))
        run("echo {} > {}/lib/{}/site-packages/projectsource.pth".format(
            SRC_DIR, VENV_SUBDIR, PYTHON_BIN))


def ensure_dir(d):
    if not exists(d):
        # note that the parent directory needs to already exist, usually by making a custom app
        # with the correct name in the webfaction control panel
        run("mkdir -p {}".format(d))


def rsync_source():
    """
    rsync the source over to the server
    """
    rsync_project(local_dir=DJANGO_PROJECT_NAME, remote_dir=DJANGO_APP_ROOT)


def checkout_and_install_libs():
    libs = {
        'domdiv': {
            'owner': 'sumpfork',
            'repo': 'dominiontabs',
            'method': 'branch',
            'branch': 'master'
        }
    }
    ensure_dir(CHECKOUT_DIR)
    with cd(CHECKOUT_DIR):
        for lib, params in libs.iteritems():
            libdir = params['repo']
            if not exists(libdir):
                run('git clone https://github.com/{}/{}.git'.format(params['owner'], params['repo']))
            with cd(libdir):
                run('git fetch origin')
                run('git checkout {}'.format(params['branch']))
                run('git pull')

                with virtualenv(VENV_DIR):
                    run_venv('pip install -U .')


@task
def webserver_stop():
    """
    Stop the webserver that is running the Django instance
    """
    run("kill $(cat {})".format(GUNICORN_PIDFILE))


def _webserver_command():
    return ('{venv_dir}/bin/gunicorn '
            '--log-file={logfile} '
            '-b 127.0.0.1:{port} '
            '-D -w {workers} --pid {pidfile} '
            '{wsgimodule}:application').format(
                **{'venv_dir': VENV_DIR,
                   'pidfile': GUNICORN_PIDFILE,
                   'wsgimodule': WSGI_MODULE,
                   'port': APP_PORT,
                   'workers': GUNICORN_WORKERS,
                   'logfile': GUNICORN_LOGFILE}
            )


@task
def webserver_start():
    """
    Starts the webserver that is running the Django instance
    """
    run(_webserver_command(), pty=False)
    run('cat {}'.format(GUNICORN_PIDFILE))


@task
def webserver_restart():
    """
    Restarts the webserver that is running the Django instance
    """
    try:
        run("kill -HUP $(cat {})".format(GUNICORN_PIDFILE))
    finally:
        webserver_start()


def _is_webserver_running():
    try:
        pid = int(open(GUNICORN_PIDFILE).read().strip())
    except (IOError, OSError):
        return False
    for ps in psutil.process_iter():
        if (ps.pid == pid and
            any('gunicorn' in c for c in ps.cmdline)
            and ps.username == USER):
            return True
    return False


@task
def local_webserver_start():
    """
    Starts the webserver that is running the Django instance, on the local machine
    """
    if not _is_webserver_running():
        local(_webserver_command())


@task
def deploy():
    install_dependencies()
    checkout_and_install_libs()
    webserver_restart()
