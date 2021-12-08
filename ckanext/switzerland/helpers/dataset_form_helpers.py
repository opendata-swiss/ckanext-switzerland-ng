# coding=UTF-8

"""
Helpers belong in this file if they are
used for rendering the dataset form
"""
import datetime
import logging
import json
import ckan.plugins.toolkit as tk
from ckan.common import _
from ckanext.switzerland.helpers.frontend_helpers import (
    get_frequency_name, get_dataset_by_identifier)
from ckanext.switzerland.helpers.localize_utils import (
    localize_by_language_order)
from ckanext.switzerland.helpers.terms_of_use_utils import (
    TERMS_OF_USE_BY_ASK, TERMS_OF_USE_OPEN, TERMS_OF_USE_BY, TERMS_OF_USE_ASK)
from dateutil.parser import parse


ADDITIONAL_FORM_ROW_LIMIT = 10
HIDE_ROW_CSS_CLASS = 'ogdch-hide-row'
SHOW_ROW_CSS_CLASS = 'ogdch-show-row'
PUBLISHER_EMPTY = {'name': '', 'url': ''}
ORGANIZATION_BASE_URL = 'https://opendata.swiss/organization/'

log = logging.getLogger(__name__)


def ogdch_get_accrual_periodicity_choices(field):
    map = [{'label': label, 'value': value}
           for value, label in get_frequency_name(get_map=True).items()]
    return map


def ogdch_get_rights_choices(field):
    return [{'label': _('* Non-commercial Allowed / Commercial Allowed / Reference Not Required'),  # noqa
             'value': TERMS_OF_USE_OPEN},
            {'label': _('* Non-commercial Allowed / Commercial With Permission Allowed / Reference Not Required'),  # noqa
             'value': TERMS_OF_USE_ASK},
            {'label': _('* Non-commercial Allowed / Commercial With Permission Allowed / Reference Required'),  # noqa
             'value': TERMS_OF_USE_BY_ASK},
            {'label': _('* Non-commercial Allowed / Commercial Allowed / Reference Required'),  # noqa
             'value': TERMS_OF_USE_BY},
            {'label':_('Non-commercial Allowed / Commercial Not Allowed / Reference Not Required'),  # noqa
             'value': 'NonCommercialAllowed-CommercialNotAllowed-ReferenceNotRequired'},  # noqa
            {'label':_('Non-commercial Allowed / Commercial Not Allowed / Reference Required'),  # noqa
             'value': 'NonCommercialAllowed-CommercialNotAllowed-ReferenceRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial Not Allowed / Reference Not Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceNotRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial Not Allowed / Reference Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial Allowed / Reference Not Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial Allowed / Reference Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialAllowed-ReferenceRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial With Permission Allowed / Reference Not Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialWithPermission-ReferenceNotRequired'},  # noqa
            {'label': _('Non-commercial Not Allowed / Commercial With Permission Allowed / Reference Required'),  # noqa
             'value': 'NonCommercialNotAllowed-CommercialWithPermission-ReferenceRequired'}]  # noqa


def ogdch_publisher_form_helper(data):
    publisher_stored = data.get('publisher')
    if publisher_stored:
        return json.loads(publisher_stored)
    pkg_extras = data.get('extras')
    if pkg_extras:
        publishers_list = [item['value']
                           for item in pkg_extras
                           if item['key'] == 'publishers']
        log.error(publishers_list)
        if publishers_list:
            publisher_old = json.loads(publishers_list[0])
            if publisher_old:
                publisher_name = publisher_old[0].get('label')
            publisher = {'name': publisher_name}
            organization = data.get('organization')
            if organization:
                publisher['url'] \
                    = _get_organization_url(organization.get('name'))
            return publisher
    return {'name': '', 'url': ''}


def _get_publisher_from_db_extras(extras):
    """
    [{u'key': u'publishers', u'value': u'[{"label": "Publisher 1"}]'},
    """
    if isinstance(extras, dict):
        publisher_fields = [(key, value.strip())
                            for key, value in extras.items()
                            if key.startswith('publisher-')
                            if value.strip() != '']
        publisher_url = [field[1]
                         for field in publisher_fields
                         if field[0] == 'publisher-url']
        if publisher_url:
            publisher_url = publisher_url[0]
        publisher_name = [field[1]
                          for field in publisher_fields
                          if field[0] == 'publisher-name']
        if publisher_name:
            publisher_name = publisher_name[0]
        return {'url': publisher_url, 'name': publisher_name}
    return None


def _build_rows_form_field(data_empty, data_list=None):
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
        row = {
            "index": str(i),
            "data": data_list[i - 1] if i <= len(data_list) else data_empty,
        }
        row["css_class"] = (
            SHOW_ROW_CSS_CLASS if (i <= number_of_rows_to_show) else HIDE_ROW_CSS_CLASS  # noqa
        )
        rows.append(row)
    return rows


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

    data_empty = {'name': '', 'email': ''}
    rows = _build_rows_form_field(
        data_empty=data_empty,
        data_list=contact_points)
    return rows


def _get_contact_points_from_storage(data):
    """
    data is expected to be stored as:
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

    data_empty = {'title': '', 'url': ''}
    rows = _build_rows_form_field(
        data_empty=data_empty,
        data_list=relations)
    return rows


def _get_relations_from_storage(data):
    """
    data is expected to be stored as:
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
        data_empty='',
        data_list=see_alsos)
    return rows


def _get_see_alsos_from_storage(data):
    """
    data is expected to be stored as:
    "see_alsos":
    [{"dataset_identifier": "443@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "444@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "10001@statistisches-amt-kanton-zuerich"}],
    """
    see_alsos_storage = data.get('see_alsos')
    see_alsos_display = []
    if see_alsos_storage:
        for see_also in see_alsos_storage:
            identifier = see_also['dataset_identifier']
            if identifier:
                try:
                    dataset_from_storage = get_dataset_by_identifier(
                        identifier=identifier)
                except Exception as e:
                    log.error("Error {} occured while retrieving identifier {}"
                              .format(e, identifier))
                else:
                    if dataset_from_storage:
                        see_alsos_display.append(
                            dataset_from_storage.get('name')
                        )
        return see_alsos_display
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
    """
    Transform isodate or posix date into the format used by the datepicker.
    Sometimes the package field `modified` has the string value 'False' or is
    empty. In these cases, an empty string is returned.
    """
    if date_value and date_value != 'False':
        date_format = tk.config.get(
            'ckanext.switzerland.date_picker_format', '%d.%m.%Y')
        try:
            # Posix timestamp
            dt = datetime.datetime.fromtimestamp(int(date_value))
            return dt.strftime(date_format)
        except ValueError:
            # ISO format date (YYYY-MM-DDTHH:MM:SS)
            dt = parse(date_value)
            return dt.strftime(date_format)
    else:
        return ""


def ogdch_temporals_form_helper(data):
    """
    Set the form field for temporals
    """
    temporals = _get_temporals_from_storage(key='temporals', data=data)
    if not temporals:
        temporals = _get_temporals_from_storage(key=('temporals',), data=data)
    if not temporals:
        temporals = get_temporals_from_form(data)

    rows = _build_rows_form_field(
        data_empty={'start_date': '', 'end_date': ''},
        data_list=temporals)
    return rows


def _get_temporals_from_storage(data, key):
    if data:
        return data.get(key, None)
    return None


def get_temporals_from_form(data):
    if isinstance(data, dict):
        temporals = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            start_date = data.get('temporal-start-date-' + str(i), '').strip()
            end_date = data.get('temporal-end-date-' + str(i), '').strip()
            if start_date or end_date:
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


def _get_organization_url(organization_name):
    return ORGANIZATION_BASE_URL + organization_name
