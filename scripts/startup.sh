#!/usr/bin/env bash
env=develop
sudo python3 setup.py build
sudo python3 setup.py $env
set -e
exec deadshot $@ -aL 90 -sp ./docs/labels/000 -do 0.300 -r RevB
