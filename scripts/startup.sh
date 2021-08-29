#!/usr/bin/env bash
env=develop
sudo python3 setup.py build
sudo python3 setup.py $env
set -e
#exec deadshot $@ -aL 90 -sp ./docs/labels/000 -do 0.300 -r RevB
exec deadshot $@ -a ./sample/005.wav -sp ./docs/dataset/labels/005 -do 0.300 -r RevD
#ffmpeg -i foo.mp3 -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav foo.wav
#deadshot -c /home/crflores/Desktop/deadshot/config/config.json
