#!/usr/bin/env bash
env=develop
sudo python3 setup.py build
sudo python3 setup.py $env
set -e
exec deadshot $@ -aL 90