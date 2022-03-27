#!/bin/bash

export APPNAME="uniticket*"

autopep8 -r --in-place $APPNAME
autoflake -r --in-place  --remove-unused-variables --expand-star-imports --remove-all-unused-imports $APPNAME

flake8 $APPNAME --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 $APPNAME --max-line-length 120 --count --statistics
