#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Updating GPG keys..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
curl -L https://packagecloud.io/github/git-lfs/gpgkey | sudo apt-key add -
wget -qO - https://www.mongodb.org/static/pgp/server-3.2.asc | sudo apt-key add -

echo "Adding archive repository for postgres..."
sudo rm /etc/apt/sources.list.d/pgdg*
echo "deb https://apt-archive.postgresql.org/pub/repos/apt trusty-pgdg-archive main" | sudo tee -a /etc/apt/sources.list
echo "deb-src https://apt-archive.postgresql.org/pub/repos/apt trusty-pgdg-archive main" | sudo tee -a /etc/apt/sources.list

echo "Removing old repository for cassandra..."
sudo rm /etc/apt/sources.list.d/cassandra*

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
if [ $CKANVERSION == 'master' ]
then
    echo "CKAN version: master"
else
    CKAN_TAG=$(git tag | grep ^ckan-$CKANVERSION | sort --version-sort | tail -n 1)
    git checkout $CKAN_TAG
    echo "CKAN version: ${CKAN_TAG#ckan-}"
fi

# update pip
pip install --upgrade pip

# install the recommended version of setuptools
if [ -f requirement-setuptools.txt ]
then
    echo "Updating setuptools..."
    pip install -r requirement-setuptools.txt
fi

python setup.py develop

pip install -r requirements.txt
pip install -r dev-requirements.txt
cd -

echo "Setting up Solr..."
docker run --name ckan_solr -p 8983:8983 -e SOLR_HEAP=1024m -v "$PWD/solr:/var/solr" -d solr:6 solr-precreate ckan
docker exec ckan_solr bash -c "cp /var/solr/* /opt/solr/server/solr/mycores/ckan/conf/"
docker restart ckan_solr

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "Installing ckanext-scheming and its requirements..."
git clone https://github.com/ckan/ckanext-scheming
cd ckanext-scheming
python setup.py develop
cd -

echo "Installing ckanext-fluent and its requirements..."
git clone https://github.com/ckan/ckanext-fluent
cd ckanext-fluent
python setup.py develop
cd -

echo "Installing ckanext-hierarchy and its requirements..."
git clone https://github.com/opendata-swiss/ckanext-hierarchy
cd ckanext-hierarchy
python setup.py develop
cd -

echo "Installing ckanext-harvest and its requirements..."
git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
python setup.py develop
pip install -r pip-requirements.txt
paster harvester initdb -c ../ckan/test-core.ini
cd -

echo "Installing ckanext-dcat and its requirements..."
git clone https://github.com/ckan/ckanext-dcat
cd ckanext-dcat
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
cd -

echo "Installing ckanext-dcatapchharvest and its requirements..."
git clone https://github.com/opendata-swiss/ckanext-dcatapchharvest
cd ckanext-dcatapchharvest
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
cd -

echo "Installing ckanext-harvester_dashboard and its requirements..."
git clone https://github.com/opendata-swiss/ckanext-harvester_dashboard
cd ckanext-harvester_dashboard
python setup.py develop
pip install -r requirements.txt
cd -

echo "Installing ckanext-xloader and its requirements..."
git clone https://github.com/ckan/ckanext-xloader
cd ckanext-xloader
python setup.py develop
pip install -r requirements.txt
cd -

echo "Installing ckanext-showcase..."
git clone https://github.com/ckan/ckanext-showcase
cd ckanext-showcase
python setup.py develop
cd -

echo "Installing ckanext-switzerland and its requirements..."
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."
