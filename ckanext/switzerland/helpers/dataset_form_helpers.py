# coding=UTF-8

"""
Helpers belong in this file if they are
used for rendering the dataset form
"""
from ckanext.switzerland.helpers.frontend_helpers import get_frequency_name  # noqa
import logging
from ckan.common import _


ADDITIONAL_FORM_ROW_LIMIT = 10
HIDE_ROW_CSS_CLASS = 'ogdch-hide-row'
SHOW_ROW_CSS_CLASS = 'ogdch-show-row'

log = logging.getLogger(__name__)


def ogdch_get_accrual_periodicity_choices(field):
    map = [{'label': label, 'value': value}
           for value, label in get_frequency_name(get_map=True).items()]
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
