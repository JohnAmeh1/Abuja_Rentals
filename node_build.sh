#!/bin/bash
set -o errexit

cd ./rentals/

if [ -d "node_modules" ]; then
    rm -rf node_modules
fi

npm install

cd ..
