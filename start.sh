#!/bin/bash
if [ -d ".venv" ]; then
    rm -rf .venv
fi

python -m venv .venv

./build-test.sh

./node_build.sh

if [ -f "testing-env.txt" ]; then
    value=$(<testing-env.txt) 
    echo "$value" > ".env.testing"
    rm -rf testing-env.txt
fi

echo "__pycache__/
__pycache__/*
*.pyc
.env.*
.venv/
.vscode/*
.env
00*.py
node_modules/
node_modules/*
install.sh
" > .gitignore