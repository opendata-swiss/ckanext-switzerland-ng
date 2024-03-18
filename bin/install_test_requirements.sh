#!/bin/bash

WORKDIR=/__w/ckanext-switzerland-ng/ckanext-switzerland-ng

pip install --upgrade pip

echo "Install ckanext-switzerland-ng"
pip install -r "$WORKDIR"/requirements.txt
pip install -r "$WORKDIR"/dev-requirements.txt
pip install -e "$WORKDIR"/

echo "Install ckanext dependencies"
pip install -e git+https://github.com/ckan/ckanext-scheming.git#egg=ckanext-scheming
pip install -e git+https://github.com/ckan/ckanext-fluent.git#egg=ckanext-fluent
pip install -e git+https://github.com/ckan/ckanext-hierarchy.git#egg=ckanext-hierarchy

# Last commit before support for Python 2 was dropped
pip install -e git+https://github.com/ckan/ckanext-harvest.git@v1.4.2#egg=ckanext-harvest
pip install -r https://raw.githubusercontent.com/ckan/ckanext-harvest/v1.4.2/requirements.txt

# Last commit before support for Python 2 was dropped
pip install -e git+https://github.com/ckan/ckanext-dcat.git@0c26bed5b7a3a7fca8e7b78e338aace096e0ebf6#egg=ckanext-dcat
pip install -r https://raw.githubusercontent.com/ckan/ckanext-dcat/0c26bed5b7a3a7fca8e7b78e338aace096e0ebf6/requirements-py2.txt

# Last commit before support for Python 2 was dropped
pip install -e git+https://github.com/ckan/ckanext-showcase.git@v1.5.2#egg=ckanext-showcase

# Last commit before support for Python 2 was dropped
pip install -e git+https://github.com/ckan/ckanext-xloader.git@16b84175005435d579607638dfe2056dda61af70#egg=ckanext-xloader
pip install -r https://raw.githubusercontent.com/ckan/ckanext-xloader/16b84175005435d579607638dfe2056dda61af70/requirements.txt

# Our ckanexts
pip install -e git+https://github.com/opendata-swiss/ckanext-dcatapchharvest.git#egg=ckanext-dcatapchharvest
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-dcatapchharvest/master/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-harvester_dashboard.git#egg=ckanext-harvester_dashboard
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-harvester_dashboard/master/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-subscribe.git#egg=ckanext-subscribe
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-subscribe/master/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-switzerland-ng.git#egg=ckanext-switzerland-ng
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-switzerland-ng/master/requirements.txt

echo "Replace default path to CKAN core config file with the one on the container"
sed -i -e 's/use = config:.*/use = config:\/srv\/app\/src\/ckan\/test-core.ini/' "$WORKDIR"/test.ini

echo "Remove plugins from CKAN config"
paster --plugin=ckan config-tool "$WORKDIR"/test.ini "ckan.plugins = "

echo "Init db"
paster --plugin=ckan db init -c "$WORKDIR"/test.ini

echo "Init harvester db"
paster --plugin=ckanext-harvest harvester initdb -c "$WORKDIR"/test.ini

echo "Re-enable plugins in CKAN config"
paster --plugin=ckan config-tool "$WORKDIR"/test.ini "ckan.plugins = ogdch ogdch_pkg ogdch_res ogdch_group ogdch_org ogdch_subscribe scheming_datasets scheming_groups scheming_organizations fluent hierarchy_display harvester_dashboard"
