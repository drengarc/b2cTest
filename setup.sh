#!/bin/bash

# Script to set up a Django project on Vagrant.

# Installation settings

PROJECT_NAME=$1

DB_NAME=$PROJECT_NAME
VIRTUALENV_NAME=$PROJECT_NAME

PROJECT_DIR=/home/vagrant/$PROJECT_NAME
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/$PROJECT_NAME

PGSQL_VERSION=9.1

# Need to fix locale so that Postgres creates databases in UTF-8
cp -p $PROJECT_DIR/etc/install/etc-bash.bashrc /etc/bash.bashrc
locale-gen en_US.UTF-8
dpkg-reconfigure locales

export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

apt-get update -y
apt-get install -y build-essential python python-setuptools git python-dev postgresql-contrib python-imaging postgresql libpq-dev python-pip gunicorn rabbitmq-server nginx supervisor fabric libjpeg-dev libxml2-dev libxslt-dev

cp -p $PROJECT_DIR/etc/install/bashrc /home/vagrant/.bashrc
su - vagrant -c "mkdir -p /home/vagrant/.pip_download_cache"

psql $PROJECT_NAME postgres << EOF
    CREATE USER b2c_test;
    CREATE DATABASE b2c_test;
EOF

pip install -r $PROJECT_DIR/requirements.txt
mkdir $PROJECT_DIR/static
chmod a+x $PROJECT_DIR/manage.py
su - vagrant -c "cd $PROJECT_DIR && ./manage.py syncdb --noinput && ./manage.py migrate"

