#!/bin/bash

WORKDIR=/__w/ckanext-switzerland-ng/ckanext-switzerland-ng

pip install --upgrade pip

echo "Install ckanext-switzerland"
pip install -e "$WORKDIR"/[dev]

echo "Install ckanext dependencies"
pip install -e git+https://github.com/ckan/ckanext-scheming.git#egg=ckanext-scheming
pip install -e git+https://github.com/ckan/ckanext-fluent.git#egg=ckanext-fluent
pip install -e git+https://github.com/ckan/ckanext-hierarchy.git#egg=ckanext-hierarchy
pip install -e git+https://github.com/ckan/ckanext-harvest.git#egg=ckanext-harvest
pip install -r https://raw.githubusercontent.com/ckan/ckanext-harvest/master/requirements.txt
pip install -e git+https://github.com/ckan/ckanext-dcat.git#egg=ckanext-dcat
pip install -e git+https://github.com/ckan/ckanext-showcase.git#egg=ckanext-showcase
pip install -e git+https://github.com/ckan/ckanext-xloader.git#egg=ckanext-xloader
pip install -r https://raw.githubusercontent.com/ckan/ckanext-xloader/master/requirements.txt

# Our ckanexts
pip install -e git+https://github.com/opendata-swiss/ckanext-dcatapchharvest.git#egg=ckanext-dcatapchharvest
pip install -e git+https://github.com/opendata-swiss/ckanext-harvester_dashboard.git#egg=ckanext-harvester_dashboard
pip install -e git+https://github.com/liip/ckanext-subscribe.git#egg=ckanext-subscribe
pip install -e git+https://github.com/opendata-swiss/ckanext-password-policy.git#egg=ckanext-password-policy

echo "Replace default path to CKAN core config file with the one on the container"
sed -i -e 's/use = config:.*/use = config:\/srv\/app\/src\/ckan\/test-core.ini/' "$WORKDIR"/test.ini

echo "Replace default database url with the one for the postgres service"
sed -i -e 's/sqlalchemy.url = .*/sqlalchemy.url = postgresql:\/\/ckan_default:pass@postgres\/ckan_test/' "$WORKDIR"/test.ini

echo "Init db"
ckan -c "$WORKDIR"/test.ini db init
