import os.path
from fabric.api import run, env, settings, cd

env.install_path = '/home/admin/opt'

def deploy():
    # TODO: update or install environment buildout with python
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
