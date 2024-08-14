#!/bin/bash

set -e

# Install pylint
echo "Installing pylint..."
pip3 install --user pylint

# Verify installation
if command -v pylint &> /dev/null
then
    echo "pylint install success!"
else
    echo "pylint installation failed, please check the error message."
fi
