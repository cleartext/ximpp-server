import os.path
from pdb import set_trace
from fabric.api import run, env, settings, cd, sudo, put, local, hide, prompt, abort

env.install_path = '/home/admin/opt'


def _run_silent(command):
    with(settings(
            hide('warnings', 'running', 'stdout', 'stderr'),
            warn_only = True)):
        return run(command)


def localhost():
    env.hosts = ['localhost']


def mblog():
    env.hosts = ['mblog.cleartext.com']


def mblog_cleartext_im():
    env.hosts = ['mblog.cleartext.im']


def cleartext_freightinvestor_com():
    env.hosts = ['cleartext.freightinvestor.com']


def deploy():
    _deploy_ssh_keys()
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
    if _run_silent('~/opt/ximpp-server/python/bin/supervisorctl status xmpp-bot | grep \'No such process\'').return_code != 0:
        # Here we check if supervisor already know about xmpp-bot
        # run update, because config may have changed
        run('~/opt/ximpp-server/python/bin/supervisorctl update')
        # then just restart
        run('~/opt/ximpp-server/python/bin/supervisorctl restart xmpp-bot')
    else:
        # Else, run update and bot will be started automatically
        run('~/opt/ximpp-server/python/bin/supervisorctl update')


def stop():
    run('~/opt/ximpp-server/python/bin/supervisorctl stop xmpp-bot')


def start():
    run('~/opt/ximpp-server/python/bin/supervisorctl start xmpp-bot')


def status():
    run('~/opt/ximpp-server/python/bin/supervisorctl status xmpp-bot')


def _deploy_ssh_keys():
    run('test -d ~/.ssh || mkdir ~/.ssh')

    if _run_silent('test ! -e ~/.ssh/git_rsa').return_code == 0:
        put('configs/ssh/git_rsa', '~/.ssh')
        put('configs/ssh/git_rsa.pub', '~/.ssh')
        put('configs/ssh/config', '/tmp/git_ssh_config')
        run('cat /tmp/git_ssh_config >> ~/.ssh/config && rm /tmp/git_ssh_config')


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

    run('rm -f %(svisor_main)s && ln -s %(svisor_main_dist)s %(svisor_main)s' % locals())
    run('rm -f %(svisor_bot)s && ln -s %(svisor_bot_dist)s %(svisor_bot)s' % locals())
    sudo('test -L %(svisor_init)s || ( ln -s %(svisor_init_dist)s %(svisor_init)s && update-rc.d supervisord defaults )' % locals())


def check_working_dir():
    with(settings(
            hide('warnings', 'running', 'stdout', 'stderr'),
            warn_only = True)):
        # checking if we are on another branch
        result = local('git branch')
        current_branch = 'master'

        for line in result.split('\n'):
            if line[0] == '*':
                current_branch = line[2:]

        if current_branch != 'master':
            result = prompt(
                'You are on a branch "%s", do you want to continue (yes/no)?' % current_branch,
                default = 'no')
            if result.lower() != 'yes':
                abort('Switch to the "master" branch (git checkout master) and try again.')

        # checking for uncommited changes
        result = local('git ls-files --stage --unmerged --killed --deleted --modified --others --exclude-standard -t')
        if result:
            result = prompt(
                'You working directory is not clean:\n%s\n\nDo you want to continue anyway (yes/no)?' % result,
                default = 'no')
            if result.lower() != 'yes':
                abort('Please, make sure that you working directory is clean, all files commited and pushed to the server.')

        # checking if we have some unpushed commits
        result = local('git cherry -v remotes/origin/%(current_branch)s %(current_branch)s' % locals())

        if result.return_code == 0:
            if result:
                result = prompt(
                    'You have not pushed these commits:\n%s\n\nDo you want to continue anyway (yes/no)?' % result,
                    default = 'no')
                if result.lower() != 'yes':
                    abort('Please, push changes to the server (git push) and try again.')
        else:
            abort('Seems, that you current branch "%s" is not pushed the the server yet, please, switch to the "master".' % current_branch)

