#!/bin/bash

sleep 15s

echo "Starting pi-frame"

cd $(dirname $0)

source ~/.virtualenvs/pimoroni/bin/activate

python3 pi-frame.py