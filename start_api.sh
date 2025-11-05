#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
python services/api-gateway/main.py
