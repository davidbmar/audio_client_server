#!/bin/bash
sudo apt install python3-venv python3-full

python3 -m venv venv


source venv/bin/activate

pip install boto3
pip install PyYAML

