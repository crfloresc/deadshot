#!/bin/bash

sudo apt-get update && \
    sudo apt-get install python3.10-venv -y

python3 -m venv .venv
. .venv/bin/activate