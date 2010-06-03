import os.path
from fabric.api import run, env, settings, cd, sudo

env.install_path = '/home/admin/opt'


def localhost():
    env.hosts = ['localhost']


def mblog():
    env.hosts = ['mblog.cleartext.com']


def deploy():
    sudo('apt-get install python2.5')
    sudo('apt-get install libssl-dev')
    _pull_sources()
    _update_buildout()
    # TODO: restart service


def _pull_sources():
    run('mkdir -p %(install_path)s' % env)
    with cd(env.install_path):
        run('test -d ximpp-server && '
            '( echo "Pulling" && cd ximpp-server && git pull )'
            ' || '
            '( echo "Initializing" && git clone git@github.com:cleartext/ximpp-server.git )'
        )


def _update_buildout():
    with cd(os.path.join(env.install_path, 'ximpp-server')):
        run('./bootstrap.sh')

