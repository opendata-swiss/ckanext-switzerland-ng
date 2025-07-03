# coding=UTF-8

"""
Helpers belong in this file if they are
used for rendering the dataset form
"""
import datetime
import json
import logging

import ckan.plugins.toolkit as tk
from ckan.plugins.toolkit import _
from dateutil.parser import parse

from ckanext.switzerland.helpers.frontend_helpers import (
    get_dataset_by_identifier,
    get_dataset_by_permalink,
    get_frequency_name,
)
from ckanext.switzerland.helpers.localize_utils import (
    LANGUAGES,
    localize_by_language_order,
)
from ckanext.switzerland.helpers.terms_of_use_utils import (
    TERMS_OF_USE_ASK,
    TERMS_OF_USE_BY,
    TERMS_OF_USE_BY_ASK,
    TERMS_OF_USE_OPEN,
)

ADDITIONAL_FORM_ROW_LIMIT = 10
HIDE_ROW_CSS_CLASS = "ogdch-hide-row"
SHOW_ROW_CSS_CLASS = "ogdch-show-row"
ORGANIZATION_URI_BASE = "https://opendata.swiss/organization/"

log = logging.getLogger(__name__)


def ogdch_get_accrual_periodicity_choices(field):
    map = [
        {"label": label, "value": value}
        for value, label in list(get_frequency_name(get_map=True).items())
    ]
    return map


def ogdch_get_license_choices(field):
    return [
        {
            "label": _(
                "Non-commercial Allowed / Commercial Allowed / Reference Not Required"
            ),
            "value": TERMS_OF_USE_OPEN,
        },
        {
            "label": _(
                "Non-commercial Allowed / Commercial With Permission Allowed / Reference Not Required"
            ),
            "value": TERMS_OF_USE_ASK,
        },
        {
            "label": _(
                "Non-commercial Allowed / Commercial With Permission Allowed / Reference Required"
            ),
            "value": TERMS_OF_USE_BY_ASK,
        },
        {
            "label": _(
                "Non-commercial Allowed / Commercial Allowed / Reference Required"
            ),
            "value": TERMS_OF_USE_BY,
        },
    ]


def ogdch_publisher_form_helper(data):
    """
    fills the publisher form snippet either from a previous form entry
    or from the db
    """

    # check for form inputs first
    publisher_form_name = {
        "fr": data.get("publisher-name-fr", ""),
        "en": data.get("publisher-name-en", ""),
        "de": data.get("publisher-name-de", ""),
        "it": data.get("publisher-name-it", ""),
    }
    publisher_form_url = data.get("publisher-url")

    if publisher_form_url or any(publisher_form_name.values()):
        return {"name": publisher_form_name, "url": publisher_form_url}

    # check for publisher from db
    publisher_stored = data.get("publisher")
    if isinstance(publisher_stored, str):
        try:
            publisher_stored = json.loads(publisher_stored)
        except json.JSONDecodeError:
            log.warning(f"Invalid JSON in publisher: {publisher_stored}")

    if isinstance(publisher_stored, dict):
        publisher_name = publisher_stored.get("name")
        # handle stored publisher data (both as dict or string)
        if isinstance(publisher_name, dict):
            return {"name": publisher_name, "url": publisher_stored.get("url", "")}
        elif isinstance(publisher_name, str):
            return {
                "name": {"de": publisher_name, "en": "", "fr": "", "it": ""},
                "url": publisher_stored.get("url", ""),
            }
        else:
            log.warning("Unexpected structure for publisher name")
            return {
                "name": {"de": "", "en": "", "fr": "", "it": ""},
                "url": publisher_stored.get("url", ""),
            }

    publisher_deprecated = _convert_from_publisher_deprecated(data)
    if publisher_deprecated:
        return publisher_deprecated

    return {"name": {"de": "", "en": "", "fr": "", "it": ""}, "url": ""}


def _convert_from_publisher_deprecated(data):
    pkg_extras = data.get("extras")
    if pkg_extras:
        publishers_in_pkg_extras = [
            item["value"] for item in pkg_extras if item["key"] == "publishers"
        ]
        if publishers_in_pkg_extras:
            publisher_labeled = json.loads(publishers_in_pkg_extras[0])
            if publisher_labeled:
                publisher_name = publisher_labeled[0].get("label")
                publisher = {"name": publisher_name}
                organization = data.get("organization")
                if organization:
                    publisher["url"] = _get_organization_url(organization.get("name"))
                return publisher
    return None


def _build_rows_form_field(data_empty, data_list=None):
    """Builds a rows form field.

    - gets a list of data to fill in the form
    - the form is built with that data
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
            SHOW_ROW_CSS_CLASS if (i <= number_of_rows_to_show) else HIDE_ROW_CSS_CLASS
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

    data_empty = {"name": "", "email": ""}
    rows = _build_rows_form_field(data_empty=data_empty, data_list=contact_points)
    return rows


def _get_contact_points_from_storage(data):
    """
    data is expected to be stored as:
    u'contact_points': [{u'email': u'tischhauser@ak-strategy.ch',
    u'name': u'tischhauser@ak-strategy.ch'}]
    """
    return data.get("contact_points")


def get_contact_points_from_form(data):
    if isinstance(data, dict):
        contact_points = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            name = data.get(f"contact-point-name-{str(i)}", "").strip()
            email = data.get(f"contact-point-email-{str(i)}", "").strip()
            if name or email:
                contact_points.append({"name": name, "email": email})
        return contact_points
    return None


def ogdch_relations_form_helper(data):
    """Sets up the form field for relations.
    "relations": [
        {"label": {"de: "text", "fr": "text", "it": "text", "en": "text"},
         "url": "https://www.admin.ch/#a20"},
        ...
    ]
    """
    relations = _get_relations_from_storage(data)
    if not relations:
        relations = get_relations_from_form(data)

    data_empty = {"label": {"de": "", "en": "", "fr": "", "it": ""}, "url": ""}
    rows = _build_rows_form_field(data_empty=data_empty, data_list=relations)
    return rows


def _get_relations_from_storage(data):
    """Relations data is expected to be stored as:
    "relations": [
        {"label": {"de: "text", "fr": "text", "it": "text", "en": "text"},
         "url": "https://www.admin.ch/#a20"},
        ...
    ]
    """
    relations = data.get("relations")
    result = []
    if relations:
        for relation in relations:
            if isinstance(relation["label"], dict):
                result.append(relation)
            else:
                result.append(
                    {
                        "label": {
                            "de": relation["label"],
                            "en": "",
                            "fr": "",
                            "it": "",
                        },
                        "url": relation["url"],
                    }
                )
    return result


def get_relations_from_form(data):
    if isinstance(data, dict):
        relations = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            label = {
                lang: data.get(f"relation-label-{str(i)}-{lang}", "")
                for lang in LANGUAGES
            }
            url = data.get(f"relation-url-{str(i)}", "")
            if any(label.values()) or url:
                relations.append({"label": label, "url": url})
        return relations
    return None


def ogdch_qualified_relations_form_helper(data):
    """Sets the form field for qualified_relations."""
    qualified_relations = _get_qualified_relations_from_storage(data)
    # see_alsos is deprecated and the new field qualified_relations should be
    # used for related datasets. Existing datasets might still have values for
    # see_alsos.
    qualified_relations.extend(_get_see_alsos_from_storage(data))
    if not qualified_relations:
        qualified_relations = get_qualified_relations_from_form(data)

    rows = _build_rows_form_field(data_empty="", data_list=qualified_relations)
    return rows


def _get_qualified_relations_from_storage(data):
    """
    data is expected to be stored as:
    "qualified_relations":
    [{
        "relation": "https://opendata.swiss/perma/443@statistisches-amt-kanton-zuerich",
        "had_role": "http://www.iana.org/assignments/relation/related"
    }]
    """
    qualified_relations_storage = data.get("qualified_relations")
    qualified_relations_display = []
    if qualified_relations_storage:
        for qualified_relation in qualified_relations_storage:
            permalink = qualified_relation["relation"]
            if permalink:
                try:
                    dataset_from_storage = get_dataset_by_permalink(permalink)
                except Exception as e:
                    log.error(
                        f"Error {e} occured while retrieving dataset with permalink "
                        f"{permalink}"
                    )
                else:
                    if dataset_from_storage:
                        qualified_relations_display.append(
                            dataset_from_storage.get("name")
                        )
        return qualified_relations_display
    return []


def _get_see_alsos_from_storage(data):
    """
    data is expected to be stored as:
    "see_alsos":
    [{"dataset_identifier": "443@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "444@statistisches-amt-kanton-zuerich"},
    {"dataset_identifier": "10001@statistisches-amt-kanton-zuerich"}],
    """
    see_alsos_storage = data.get("see_alsos")
    see_alsos_display = []
    if see_alsos_storage:
        for see_also in see_alsos_storage:
            identifier = see_also["dataset_identifier"]
            if identifier:
                try:
                    dataset_from_storage = get_dataset_by_identifier(
                        identifier=identifier
                    )
                except Exception as e:
                    log.error(
                        f"Error {e} occured while retrieving identifier {identifier}"
                    )
                else:
                    if dataset_from_storage:
                        see_alsos_display.append(dataset_from_storage.get("name"))
        return see_alsos_display
    return []


def get_qualified_relations_from_form(data):
    if isinstance(data, dict):
        qualified_relations = [
            value.strip()
            for key, value in list(data.items())
            if key.startswith("qualified-relation-")
            if value.strip() != ""
        ]
        return qualified_relations
    return None


def ogdch_date_form_helper(date_value):
    """
    Transform isodate or posix date into the format used by the date picker.
    Sometimes the package field `modified` has the string value 'False' or is
    empty. In these cases, an empty string is returned.
    """
    if date_value and date_value != "False":
        date_format = tk.config.get(
            "ckanext.switzerland.date_picker_format", "%d.%m.%Y"
        )
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
    temporals = _get_temporals_from_storage(key="temporals", data=data)
    if not temporals:
        temporals = _get_temporals_from_storage(key=("temporals",), data=data)
    if not temporals:
        temporals = get_temporals_from_form(data)

    rows = _build_rows_form_field(
        data_empty={"start_date": "", "end_date": ""}, data_list=temporals
    )
    return rows


def _get_temporals_from_storage(data, key):
    if data:
        return data.get(key, None)
    return None


def get_temporals_from_form(data):
    if isinstance(data, dict):
        temporals = []
        for i in range(1, ADDITIONAL_FORM_ROW_LIMIT + 1):
            start_date = data.get(f"temporal-start-date-{str(i)}", "").strip()
            end_date = data.get(f"temporal-end-date-{str(i)}", "").strip()
            if start_date or end_date:
                temporals.append({"start_date": start_date, "end_date": end_date})
        return temporals
    return None


def ogdch_dataset_title_form_helper(data):
    if isinstance(data, dict):
        title = data.get("title")
        if title:
            return localize_by_language_order(title)
        return ""


def _get_organization_url(organization_name):
    return ORGANIZATION_URI_BASE + organization_name


def ogdch_multiple_text_form_helper(value):
    """Ensures that the value of a multiple text field is a list.

    If an edited dataset has not been saved because of validation errors, we
    return to the edit page. Unedited fields are filled in with their saved
    values, while edited fields are filled with the form data we got from the
    browser. In this case, if the value of an edited multiple text field is a
    single string, we just get that string, not a list containing the string.
    This messes up the multiple_text.html form snippet, so let's prevent it.
    """
    if not isinstance(value, list):
        value = [value]
    return value
