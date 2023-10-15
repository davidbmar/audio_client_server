#!/bin/bash
pip install gunicorn
gunicorn -w 4 mainScreen:app
