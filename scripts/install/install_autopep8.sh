#!/bin/bash

set -e

# Install autopep8
echo "Installing autopep8..."
pip3 install --user autopep8

# Verify installation
if command -v autopep8 &> /dev/null
then
    echo "autopep8 install success!"
else
    echo "autopep8 installation failed, please check the error message."
fi
