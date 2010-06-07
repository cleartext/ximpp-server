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

    restart()


def restart():
    run('~/opt/ximpp-server/python/bin/supervisorctl restart xmpp-bot')


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
    run('mkdir -p ~/log')
    run('mkdir -p ~/run')
    run('mkdir -p ~/etc/supervisor.d')

    configs = os.path.join(
        env.install_path, 'ximpp-server', 'configs'
    )
    svisor_main = '~/etc/supervisord.conf'
    svisor_main_dist = os.path.join(configs, 'supervisord', 'common.conf')

    svisor_bot = '~/etc/supervisor.d/bot.conf'
    svisor_bot_dist = os.path.join(configs, 'supervisord', env.host + '.conf')

    svisor_init = '/etc/init.d/supervisord'
    svisor_init_dist = os.path.join(configs, 'supervisord', 'init.d.conf')

    run('test -e %(svisor_main)s || ln -s %(svisor_main_dist)s %(svisor_main)s' % locals())
    run('test -e %(svisor_bot)s || ln -s %(svisor_bot_dist)s %(svisor_bot)s' % locals())
    sudo('test -e %(svisor_init)s || ( ln -s %(svisor_init_dist)s %(svisor_init)s && update-rc.d supervisord defaults )' % locals())
