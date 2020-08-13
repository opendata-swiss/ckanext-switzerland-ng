"""
helpers for the plugin logic
"""
import ckan.plugins.toolkit as tk


def get_org_count():
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    orgs = tk.get_action('organization_list')(req_context, {})
    return len(orgs)


def get_dataset_count(dataset_type='dataset'):
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    fq = ''.join(['+dataset_type:', dataset_type])
    packages = tk.get_action('package_search')(
        req_context,
        {'fq': fq}
    )
    return packages['count']
