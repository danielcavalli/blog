#!/bin/bash
# Build script wrapper for Unix/Linux/Mac
cd "$(dirname "$0")"
python _source/build.py "$@"
