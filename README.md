ckanext-switzerland
===================

CKAN extension for DCAT-AP Switzerland, templates and different plugins for [opendata.swiss](https://opendata.swiss).

## Requirements

- CKAN 2.11+
- ckanext-scheming
- ckanext-fluent

## Installation

To install ckanext-switzerland:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-switzerland-ng Python package into your virtual environment:

     git clone https://github.com/opendata-swiss/ckanext-switzerland-ng.git
     cd ckanext-switzerland-ng
     pip install -e .

3. Add relevant plugins to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``). This package contains several
   plugins. See ``project.entry-points."ckan.plugins"`` in ``pyproject.toml``
  for an up-to-date list.

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload

## Config Settings

See `ckanext/switzerland/config_declaration.yaml`.

## Development Installation

To install ckanext-switzerland for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/opendata-swiss/ckanext-switzerland-ng.git
    cd ckanext-switzerland-ng
    pip install -e .[dev]

## Update Format-Mapping

To update the Format-Mapping edit the [format-mapping.yaml](/ckanext/switzerland/helpers/format_mapping.yaml), following
the [YAML-Syntax](http://docs.ansible.com/ansible/latest/YAMLSyntax.html). You can check if your changes are valid by
pasting the contents of the required changes into a Syntax-Checker, e.g. [YAML Syntax-Checker](http://www.yamllint.com/).
Submit a Pull-Request following our [Contribution-Guidelines](CONTRIBUTING.md).

## Update translations

To generate an updated ckanext-switzerland.pot file inside the Docker
container, use the following commands:

    docker-compose exec ckan bash
    source /usr/lib/ckan/venv/bin/activate
    cd /usr/lib/ckanext/ckanext-switzerland-ng/
    python setup.py extract_messages

Copy any new strings that you want to translate from the new
`ckanext-switzerland.pot` into the `ckanext-switzerland.po` file for each
language, and add the translations.

After that compile the po files into mo files:

    python setup.py compile_catalog

Log out of the ckan container (ctrl+D) and restart it for the new translations
to be used:

    docker-compose restart ckan

## Add users as members to groups

For opendata.swiss we use groups in the sense of categories. Therefore we need any user to be able to add their datasets
to any group. For that they need to be a member of the group.

Users with the role `admin` are automatically added as `admin` to each group.

```bash
# add a specific user who is not an admin as member to a specific group:
$ curl {ckan_url}/api/3/action/ogdch_add_users_to_groups?user_id=greta.mayer&user_id=administration

# add all users that are not admins as members to a specific group:
$ curl {ckan_url}/api/3/action/ogdch_add_users_to_groups?group_id=administration

# add a specific user who is not an admin as member to all available groups:
$ curl {ckan_url}/api/3/action/ogdch_add_users_to_groups?user_id=greta.mayer

# add all users that are not admins as members to all specific groups:
$ curl {ckan_url}/api/3/action/ogdch_add_users_to_groups
```
