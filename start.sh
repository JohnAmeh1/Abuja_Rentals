#!/bin/bash
if [ -d ".venv" ]; then
    rm -rf .venv
fi

python -m venv .venv

pip install -r requirements.txt
python manage.py collectstatic --no-input

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

echo "
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

CLOUDINARY_CLOUD_NAME = ddhjg0j3u
CLOUDINARY_API_KEY = 228448685218287
CLOUDINARY_API_SECRET = ZqaL-BCrilQGT2qdHFdaCrHfv6o

EMAIL_HOST_USER=favourfasi46@gmail.com
BREVO_API_KEY=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
" > .env.development

echo "DJANGO_ENV=development" > .env