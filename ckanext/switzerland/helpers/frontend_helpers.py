"""
helpers belong in this file if they
are used in frontend templates
"""
from collections import OrderedDict
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import json
from ckan.common import _
from babel import numbers

from ckan.lib.formatters import localised_nice_date
from ckan.lib.helpers import lang, url_for, localised_number
import ckan.lib.i18n as i18n
from ckanext.hierarchy.helpers import group_tree
import ckanext.switzerland.helpers.localize_utils as ogdch_loc_utils
import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils
from dateutil.parser import parse, ParserError

import logging
log = logging.getLogger(__name__)

# these bookmarks can be used in the wordpress page
# for the terms of use
mapping_terms_of_use_to_pagemark = {
    ogdch_term_utils.TERMS_OF_USE_OPEN: '#terms_open',
    ogdch_term_utils.TERMS_OF_USE_BY: '#terms_by',
    ogdch_term_utils.TERMS_OF_USE_ASK: '#terms_ask',
    ogdch_term_utils.TERMS_OF_USE_BY_ASK: '#terms_by_ask',
}


def get_group_count():
    '''
    Return the number of groups
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    groups = tk.get_action('group_list')(req_context, {})
    return len(groups)


def get_localized_org(org_id=None, include_datasets=False):
    if not org_id or org_id is None:
        return {}
    try:
        return logic.get_action('organization_show')(
            {'for_view': True},
            {'id': org_id, 'include_datasets': include_datasets}
        )
    except (logic.NotFound, logic.ValidationError,
            logic.NotAuthorized, AttributeError):
        return {}


def localize_json_facet_title(facet_item):
    # json.loads tries to convert numbers in Strings to integers. At this point
    # we only need to deal with Strings, so we let them be Strings.
    try:
        int(facet_item['display_name'])
        return facet_item['display_name']
    except (ValueError, TypeError):
        pass
    try:
        lang_dict = json.loads(facet_item['display_name'])
        if type(lang_dict) == bool:
            # json.loads converts the string 'false' or 'true' into a boolean
            # value, which is not what we want for a facet title.
            return _(str(lang_dict))

        return ogdch_loc_utils.get_localized_value_from_dict(
            lang_dict,
            lang_code=lang(),
            default=facet_item['display_name']
        )
    except BaseException:
        return facet_item['display_name']


def get_frequency_name(identifier=None, get_map=False):
    frequencies = OrderedDict([
        ('http://publications.europa.eu/resource/authority/frequency/OTHER', _('Other')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/WEEKLY', _('Weekly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/ANNUAL', _('Annual')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/ANNUAL_2', _('Semiannual')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/ANNUAL_3', _('Three times a year')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/BIENNIAL', _('Biennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/BIMONTHLY', _('Bimonthly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/BIWEEKLY', _('Biweekly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/CONT', _('Continuous')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/DAILY', _('Daily')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/DAILY_2', _('Twice a day')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/IRREG', _('Irregular')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/MONTHLY', _('Monthly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/MONTHLY_2', _('Semimonthly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/MONTHLY_3', _('Three times a month')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/NEVER', _('Never')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/OP_DATPRO', _('Provisional data')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/QUARTERLY', _('Quarterly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/TRIENNIAL', _('Triennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/UNKNOWN', _('Unknown')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/UPDATE_CONT', _('Continuously updated')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/WEEKLY_2', _('Semiweekly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/WEEKLY_3', _('Three times a week')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/QUINQUENNIAL', _('Quinquennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/DECENNIAL', _('Decennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/HOURLY', _('Hourly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/QUADRENNIAL', _('Quadrennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/BIHOURLY', _('Bihourly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/TRIHOURLY', _('Trihourly')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/BIDECENNIAL', _('Bidecennial')),  # noqa
        ('http://publications.europa.eu/resource/authority/frequency/TRIDECENNIAL', _('Tridecennial')),  # noqa
    ])
    if get_map:
        return frequencies
    try:
        return frequencies[identifier]
    except KeyError:
        return identifier


def get_political_level(political_level):
    political_levels = {
        'confederation': _('Confederation'),
        'canton': _('Canton'),
        'commune': _('Commune'),
        'other': _('Other')
    }
    return political_levels.get(political_level, political_level)


def get_terms_of_use_icon(terms_of_use):
    term_to_image_mapping = {
        ogdch_term_utils.TERMS_OF_USE_OPEN: {  # noqa
            'title': _('Open use'),
            'icon': 'terms_open',
        },
        ogdch_term_utils.TERMS_OF_USE_BY: {  # noqa
            'title': _('Open use. Must provide the source.'),
            'icon': 'terms_by',
        },
        ogdch_term_utils.TERMS_OF_USE_ASK: {  # noqa
            'title': _('Open use. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_ask',
        },
        ogdch_term_utils.TERMS_OF_USE_BY_ASK: {  # noqa
            'title': _('Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_by-ask',
        },
        ogdch_term_utils.TERMS_OF_USE_CLOSED: {
            'title': _('Closed data'),
            'icon': 'terms_closed',
        },
    }
    term_id = ogdch_term_utils.simplify_terms_of_use(terms_of_use)
    return term_to_image_mapping.get(term_id, None)


def get_terms_of_use_url(terms_of_use):
    terms_of_use_url = url_for('/terms-of-use')
    pagemark = mapping_terms_of_use_to_pagemark.get(terms_of_use)
    if pagemark:
        terms_of_use_url += pagemark
    return terms_of_use_url


def get_dataset_terms_of_use(pkg):
    rights = logic.get_action('ogdch_dataset_terms_of_use')(
        {}, {'id': pkg['id']})
    return rights['dataset_rights']


def get_dataset_by_identifier(identifier):
    try:
        return logic.get_action('ogdch_dataset_by_identifier')(
            {'for_view': True},
            {'identifier': identifier}
        )
    except logic.NotFound:
        return None


def get_readable_file_size(num, suffix='B'):
    if not num:
        return False
    try:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            num = float(num)
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)
    except ValueError:
        return False


def get_piwik_config():
    return {
        'url': tk.config.get('piwik.url', False),
        'site_id': tk.config.get('piwik.site_id', False),
        'custom_dimension_action_organization_id': tk.config.get('piwik.custom_dimension_action_organization_id', False),  # noqa
        'custom_dimension_action_dataset_id': tk.config.get('piwik.custom_dimension_action_dataset_id', False),  # noqa
        'custom_dimension_action_format_id': tk.config.get('piwik.custom_dimension_action_format_id', False)  # noqa
    }


def ogdch_localised_number(number):
    # use swissgerman formatting rules when current language is german
    if i18n.get_lang() == 'de':
        return numbers.format_number(number, locale='de_CH')
    else:
        return localised_number(number)


def ogdch_render_tree(organizations=None):
    """
    Returns HTML for a hierarchy of given organizations
    """
    if organizations:
        top_nodes = ogdch_group_tree_selective(organizations, group_tree(
            type_='organization'))
    else:
        top_nodes = ogdch_group_tree()
    return _render_tree(top_nodes)


def _render_tree(top_nodes):
    """
    Renders a tree of nodes. 10x faster than Jinja/organization_tree.html
    Note: avoids the slow url_for routine.
    """
    html = '<ul id="organizations-list">'
    for node in top_nodes:
        html += _render_tree_node(node)
    return html + '</ul>'


def _render_tree_node(node):
    html = '<div class="organization-row">'
    html += '<a href="/%s/organization/%s">%s</a>' % (i18n.get_lang(), node['name'], node['title'])  # noqa
    html += '</div>'
    if node['children']:
        html += '<ul>'
        for child in node['children']:
            html += _render_tree_node(child)
        html += '</ul>'
    html = '<li id="node_%s" class="organization">%s</li>' % (node['name'], html)  # noqa
    return html


def ogdch_group_tree(type_='organization'):
    organizations = tk.get_action('group_tree')(
        {},
        {'type': type_, 'all_fields': True}
    )
    organizations = get_sorted_orgs_by_translated_title(organizations)
    return organizations


def ogdch_group_tree_selective(organizations, group_tree_list):
    """"
    Return a group tree filtered to include the given organizations.
    If a sub-organization should be included, its parent is included too.
    """
    def filter(group_tree_list, name_list):
        new_group_tree_list = []
        for tree in group_tree_list:
            new_children = []
            for child in tree.get('children', []):
                if child.get('name', "") in name_list:
                    new_children.append(child)
            if tree.get('name', "") in name_list or\
                    len(new_children) > 0:
                tree['children'] = new_children
                new_group_tree_list.append(tree)
        return new_group_tree_list

    selected_names = [o.get('name', None) for o in organizations]

    group_tree_list = filter(group_tree_list, selected_names)
    group_tree_list = get_sorted_orgs_by_translated_title(group_tree_list)
    return group_tree_list


def get_sorted_orgs_by_translated_title(organizations):
    for organization in organizations:
        organization['title'] = ogdch_loc_utils.get_localized_value_from_json(organization['title'], i18n.get_lang())  # noqa
        if organization['children']:
            organization['children'] = get_sorted_orgs_by_translated_title(organization['children'])  # noqa

    organizations.sort(key=lambda org: ogdch_loc_utils.strip_accents(org['title'].lower()), reverse=False)  # noqa
    return organizations


def get_localized_newsletter_url():
    current_language = lang()
    newsletter_url = {
       'en': None,
       'de': 'https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/ogd/newsmail.html',  # noqa
       'fr': 'https://www.bfs.admin.ch/bfs/fr/home/services/ogd/newsmail.html',
       'it': 'https://www.bfs.admin.ch/bfs/it/home/servizi/ogd/newsmail.html',
    }
    return newsletter_url[current_language]


def get_localized_value_for_display(value):
    lang_code = lang()
    if isinstance(value, dict):
        return ogdch_loc_utils.get_localized_value_from_dict(value, lang_code)
    try:
        value = json.loads(value)
        return ogdch_loc_utils.get_localized_value_from_dict(value, lang_code)
    except ValueError:
        return value


def get_localized_date(date_string):
    """
    Take a date string and return a localized date, e.g. '24. Juni 2020'.
    `parse` should be able to handle various date formats, including
    DD.MM.YYYY, DD.MM.YYY (necessary for collections with pre-1000 temporals)
    and DD.MM.YY (in this case, it assumes the century isn't specified and
    the year is between 50 years ago and 49 years in the future. This means
    that '01.01.60' => 01.01.2060, and '01.01.90' => 01.01.1990).
    """
    try:
        dt = parse(date_string, dayfirst=True)
        return localised_nice_date(dt, show_date=True, with_hours=False)
    except (TypeError, ParserError):
        return ''
