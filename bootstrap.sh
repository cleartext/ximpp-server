#!/bin/bash

BASE=$(readlink -f $(dirname $0))
VERBOSITY=-vv

if [ ! -d "$BASE/python" ]; then
    echo ================================
    echo Creating buildout for python
    echo ================================

    mkdir "$BASE/python"
    ln -s "$BASE/configs/buildout/buildout_python.cfg" "$BASE/python/buildout.cfg"
    python "$BASE/bootstrap.py" --distribute -c "$BASE/python/buildout.cfg"
fi

echo ================================
echo Updating python buildout
echo ================================
"$BASE/python/bin/buildout" $VERBOSITY -c "$BASE/python/buildout.cfg"


if [ ! -d "$BASE/env" ]; then
    echo ================================
    echo Creating buildout for bot
    echo ================================

    mkdir "$BASE/env"
    ln -s "$BASE/configs/buildout/buildout.cfg" "$BASE/env/buildout.cfg"
    "$BASE/python/bin/python" "$BASE/bootstrap.py" --distribute -c "$BASE/env/buildout.cfg"
fi

echo ================================
echo Updating bot buildout
echo ================================
"$BASE/env/bin/buildout" $VERBOSITY -c "$BASE/env/buildout.cfg"

