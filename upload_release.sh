#!/usr/bin/env bash

set -e

[[ -d "dist/" ]] && rm -r dist/

python setup.py sdist bdist_wheel

# https://pypi.org/project/twine/
twine upload dist/*
