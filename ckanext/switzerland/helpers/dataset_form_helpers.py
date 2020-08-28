# coding=UTF-8

"""
Helpers belong in this file if they are
used for rendering the dataset form
"""
from ckanext.switzerland.helpers.frontend_helpers import get_frequency_name  # noqa
import logging
from ckan.logic import NotFound, get_action
from ckan.common import _
from ckanext.switzerland.helpers.frontend_helpers import (
    get_frequency_name, get_dataset_by_identifier)
from ckanext.switzerland.helpers.localize_utils import localize_by_language_order


ADDITIONAL_FORM_ROW_LIMIT = 10
HIDE_ROW_CSS_CLASS = 'ogdch-hide-row'
SHOW_ROW_CSS_CLASS = 'ogdch-show-row'

log = logging.getLogger(__name__)


def ogdch_get_accrual_periodicity_choices(field):
    map = [{'label': label, 'value': value}
           for value, label in get_frequency_name(get_map=True).items()]
    return map


def ogdch_get_theme_choices(field):
    context = {'for_view': True,}
    data_dict = {'all_fields': True}
    try:
        themes = get_action('group_list')(context, data_dict)
    except NotFound:
        return None
    map = [{'label': theme.get('title'), 'value': theme.get('name')} for theme in themes]
    return map


def ogdch_publishers_form_helper(data):
    publishers = _get_publishers_from_storage(data)
    if not publishers:
        publishers = get_publishers_from_form(data)

    rows = _build_rows_form_field(
        first_label=_('Publisher'),
        default_label=_('Another Publisher'),
        data_empty='',
        data_list=publishers)
    return rows


def _build_rows_form_field(first_label, default_label, data_empty, data_list=None):
    """builds a rows form field
    - gets a list of data to fill in the form
    - the form is build with that data
    - rows that are empty are set to hidden
    - when there is no data the first row is displayed
    """
    data_list = data_list if data_list else []
    number_of_rows_to_show = len(data_list) if data_list else 1
    rows = []
    for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
        row = {'index':str(i), 'data': data_list[i - 1] if i <= len(data_list) else data_empty }
        row['css_class'] = SHOW_ROW_CSS_CLASS if (i <= number_of_rows_to_show) else HIDE_ROW_CSS_CLASS
        row['label'] = first_label if i == 1 else default_label
        rows.append(row)
    return rows


def _get_publishers_from_storage(data):
    """
    the data is expected to be stored as: "publishers":
    [{u'label': u'amt-fur-mobilitat-kanton-basel-stadt'}]
    """
    publishers_stored_data = data.get('publishers')
    if publishers_stored_data:
        publishers = [item['label'] for item in publishers_stored_data]
        return publishers
    return None


def get_publishers_from_form(data):
    if isinstance(data, dict):
        publishers = [value.strip()
                      for key, value in data.items()
                      if key.startswith('publisher-')
                      if value.strip() != '']
        return publishers
    return None


def ogdch_contact_points_form_helper(data):
    """
    sets the form field for contact_points
    u'contact_points':
    [{u'email': u'opendata@bs.ch',
    u'name': u'Fachstelle f\\xfcr OGD Basel-Stadt'}],
    """
    contact_points = _get_contact_points_from_storage(data)
    if not contact_points:
        contact_points = get_contact_points_from_form(data)

    label = {'name': _('Name'), 'email': _('Email')}
    data_empty = {'name': '', 'email': ''}
    rows = _build_rows_form_field(
        first_label=label,
        default_label=label,
        data_empty=data_empty,
        data_list=contact_points)
    return rows


def _get_contact_points_from_storage(data):
    """data is expected to be stored as:
    u'contact_points': [{u'email': u'tischhauser@ak-strategy.ch',
    u'name': u'tischhauser@ak-strategy.ch'}]
    """
    return data.get('contact_points')


def get_contact_points_from_form(data):
    if isinstance(data, dict):
        contact_points = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            name = data.get('contact-point-name-' + str(i), '').strip()
            email = data.get('contact-point-email-' + str(i), '').strip()
            if (name or email):
                contact_points.append(
                    {'name': name,
                     'email': email})
        return contact_points
    return None


def ogdch_relations_form_helper(data):
    """
    sets the form field for relations
    "relations": [
    {"label": "legal_basis", "url": "https://www.admin.ch/#a20"},
    {"label": "legal_basis", "url": "https://www.admin.ch/#a21"}]
    """
    relations = _get_relations_from_storage(data)
    if not relations:
        relations = get_relations_from_form(data)

    label = {'title': _('Title'), 'url': _('Url')}
    data_empty = {'title': '', 'url': ''}
    rows = _build_rows_form_field(
        first_label=label,
        default_label=label,
        data_empty=data_empty,
        data_list=relations)
    return rows


def _get_relations_from_storage(data):
    """data is expected to be stored as:
    "relations": [
    {"label": "legal_basis", "url": "https://www.admin.ch/#a20"},
    {"label": "legal_basis", "url": "https://www.admin.ch/#a21"}]
    """
    relations = data.get('relations')
    if relations:
        return [{"title": relation["label"], "url": relation["url"]}
                for relation in relations]
    return None


def get_relations_from_form(data):
    if isinstance(data, dict):
        relations = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            title = data.get('relation-title-' + str(i), '')
            url = data.get('relation-url-' + str(i), '')
            if (title or url):
                relations.append(
                    {'title': title,
                     'url': url})
        return relations
    return None


def ogdch_see_alsos_form_helper(data):
    """
    sets the form field for see_alsos
    """
    see_alsos = _get_see_alsos_from_storage(data)
    if not see_alsos:
        see_alsos = get_see_alsos_from_form(data)

    rows = _build_rows_form_field(
        first_label=_('Related dataset'),
        default_label=_('Another related dataset'),
        data_empty = '',
        data_list=see_alsos)
    return rows


def _get_see_alsos_from_storage(data):
    """data is expected to be stored as:
    "see_alsos": [{"dataset_identifier": "443@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "444@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "10001@statistisches-amt-kanton-zuerich"}],
    """
    see_alsos = data.get('see_alsos')
    if see_alsos:
        for dataset in see_alsos:
            dataset = get_dataset_by_identifier(identifier=dataset["dataset_identifier"])
            if dataset:
                see_alsos.append(dataset.name)
        return see_alsos
    return None


def get_see_alsos_from_form(data):
    if isinstance(data, dict):
        see_alsos = [value.strip()
                     for key, value in data.items()
                     if key.startswith('see-also-')
                     if value.strip() != '']
        return see_alsos
    return None


def ogdch_date_form_helper(date_value):
    """transform isodate into display date
    u'2012-12-31T00:00:00' to 2012-12-31,
    """
    if date_value:
        return date_value.split('T')[0]
    else:
        return ""


def ogdch_temporals_form_helper(data):
    """
    sets the form field for temporals
    """
    temporals = _get_temporals_from_storage(key='temporals', data=data)
    if not temporals:
        temporals = _get_temporals_from_storage(key=('temporals',), data=data)
    if not temporals:
        temporals = get_temporals_from_form(data)

    label = {'start_date': _('Start-Date'), 'end_date': _('End-Date')}
    rows = _build_rows_form_field(
        first_label=label,
        default_label=label,
        data_empty = {'start_date': '', 'end_date': ''},
        data_list=temporals)
    return rows


def _get_temporals_from_storage(data, key):
    """data is expected to be stored as:
    "temporals": [{"start_date": "1981-06-14T00:00:00",
     "end_date": "2020-09-27T00:00:00"}]
    """
    if data:
        temporals = data.get(key)
        if temporals:
            temporals = [
                {'start_date': ogdch_date_form_helper(temporal['start_date']),
                 'end_date': ogdch_date_form_helper(temporal['end_date'])}
                for temporal in temporals
            ]
            return temporals
    return None


def get_temporals_from_form(data):
    if isinstance(data, dict):
        temporals = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            start_date = data.get('temporal-start-date-' + str(i), '').strip()
            end_date = data.get('temporal-end-date-' + str(i), '').strip()
            if (start_date or end_date):
                temporals.append(
                    {'start_date': start_date,
                     'end_date': end_date})
        return temporals
    return None


def ogdch_dataset_title_form_helper(data):
    if isinstance(data, dict):
        title = data.get('title')
        if title:
            return localize_by_language_order(title)
        return ''
