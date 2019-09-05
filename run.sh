#!/bin/bash
find . -type f | grep ".pyc$" | xargs rm
./manage.py runserver
