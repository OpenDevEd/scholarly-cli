#!/bin/bash
echo Installing scholarly
pip3 install scholarly > /dev/null
echo Installing scholarly-cli
pip3 install -e .
