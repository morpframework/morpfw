#!/bin/bash

if [ ! -d "./venv" ];then
    echo "Initializing Virtualenv"
    virtualenv -p python3 venv
fi

if [ ! -f "./venv/bin/py.test" ];then
    echo "Installing PyTest"
    ./venv/bin/pip install pytest
fi

if [ ! -f "./bin/buildout" ];then
    echo "Bootstrap Buildout"
    ./venv/bin/python bootstrap-buildout.py
fi

echo "Starting Build ..."

./bin/buildout -vvv
