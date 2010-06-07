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
    _update_supervisord()
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
        local('tar -zcf /tmp/eggs.tar.gz eggs')
        put('/tmp/eggs.tar.gz', '/tmp')
        run('tar -zxf /tmp/eggs.tar.gz')

    with cd(os.path.join(env.install_path, 'ximpp-server')):
        run('./bootstrap.sh')


def _update_supervisord():
    sudo('mkdir -p ~/log')
    sudo('mkdir -p ~/run')
    sudo('mkdir -p ~/etc/supervisor.d')

    configs = os.path.join(
        env.install_path, 'ximpp-server', 'configs'
    )
    svisor_main = '~/env/supervisord.conf'
    svisor_main_dist = os.path.join(configs, 'supervisord', 'common.conf')

    svisor_bot = '~/env/supervisor.d/bot.conf'
    svisor_bot_dist = os.path.join(configs, 'supervisord', env.host + '.conf')

    sudo('test -e %(svisor_main)s || ln -s %(svisor_main_dist)s %(svisor_main)s' % locals())
    sudo('test -e %(svisor_bot)s || ln -s %(svisor_bot_dist)s %(svisor_bot)s' % locals())
