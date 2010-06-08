Cleartext Microblogging Server
==============================

Deployment
----------

* Setup the MySQL database on the localhost.
* Fill the initial database schema.
* Execute additional SQL statements from file `schema.sql`.
* Generate SSH key and add it as a DeploymentKey on the GitHub.
* Run `ssh github.com` and answer `yes` if it asks to add github to
  the list of known hosts.
* On dev machine edit `fabfile.py` and add function which setup
  `env.hosts` variable to the list of the target hosts. Remember
  the functions name as it will be used in the last step.
* For each host, create a config files:
  - configs/bot/mblog.cleartext.com.cfg you can use this one, as
    example, just rename replacing one host to another. You should
    change the content of the file as well.
  - configs/supervisord/mblog.cleartext.com.conf the same thing
    as with previous config. Rename and change the content.

* These steps are optional and needed only once, if there is not
  [fabric](http://fabfile.org) on the system.
  - Run ./bootstrap.sh on the dev machine to create `python`
    buildout environment.
  - Run `rm python/buildout.cfg`
  - Run `ln -s configs/buildout/buildout_python.cfg python/buildout.cfg`
  - Update buildout `python/bin/buildout -v -c python/buildout.cfg`
* And finally, run `python/bin/fab func_name deploy`. This will go to every
  machine, listed in `env.hosts` variable (remember, you set it in the
  `func_name` function?) install neccessary debian packages, checkout the
  bot's sources, build the python2.6, copy all eggs from the dev machine,
  setup the supervisord, and finally, start the bot.

Continuous integration
----------------------

As new changes are introduced in the codebase, all you need to do is to
push them on the GitHub and to run `python/bin/fab client_name deploy`.

Also, you can add such function to the `fabfile.py` to upgrade all clients machines:

    def all_clients():
        env.hosts = ['clent1', 'client2', ...]

ChangeLog
---------

- Added MySQL backend (and merged with main code).
- Follow, unfollow, followers and following commands.
- Added search add, delete and list.

