#!/bin/bash
sudo apt update
sudo apt install zip
mkdir -p python/lib/python3.10/site-packages
pip install requests -t python/lib/python3.10/site-packages/
zip -r requests_layer.zip python

