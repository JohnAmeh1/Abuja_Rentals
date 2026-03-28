# Exit on error
set -o errexit

cd ./rentals/

rm -rf node_modules

npm install

cd ..
