import os.path
from fabric.api import run, env, settings, cd, sudo, put, local

env.install_path = '/home/admin/opt'


def localhost():
    env.hosts = ['localhost']


def mblog():
    env.hosts = ['mblog.cleartext.com']


def deploy():
    sudo('apt-get update')
    sudo('apt-get --yes install python2.5')
    sudo('apt-get --yes install python2.5-dev')
    sudo('apt-get --yes install libssl-dev')
    sudo('apt-get --yes install git-core')
    sudo('apt-get --yes install make')

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
    with cd('~/'):
        local('tar -zcf eggs.tar.gz eggs')
        put('eggs.tar.gz', '/tmp')
        run('tar -zxvf /tmp/eggs.tar.gz')

    with cd(os.path.join(env.install_path, 'ximpp-server')):
        run('./bootstrap.sh')

