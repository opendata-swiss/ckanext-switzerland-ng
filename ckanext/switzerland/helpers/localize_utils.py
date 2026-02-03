"""
localization functions that don't need the request object
"""

import json
import unicodedata

LANGUAGES = {"de", "fr", "it", "en"}


def parse_json_attributes(ckan_dict):
    """turn attribute values from json
    to python structures"""
    for key, value in ckan_dict.items():
        ckan_dict[key] = parse_json(value)
    return ckan_dict


def get_language_priorities():
    language_priorities = ["en", "de", "fr", "it"]
    return language_priorities


def parse_json(value, default_value=None):
    """If the value is a json string, return a dict.
    Otherwise, return the value.
    """
    try:
        json_value = json.loads(value)
        if isinstance(json_value, int):
            # If the value is a string with a number, e.g. "5", json.loads will
            # convert it into an int, but we want the original string.
            return value
        return json_value
    except (ValueError, TypeError, AttributeError):
        if default_value is not None:
            return default_value

        return value


def lang_to_string(data_dict, attribute):
    """make a long string with all 4 languages of an attribute"""
    value_dict = data_dict.get(attribute, {})

    # Handle case where value is already a string
    if isinstance(value_dict, str):
        return value_dict

    # Handle dictionary with language keys
    if isinstance(value_dict, dict):
        return (
            f"{value_dict.get('de', '')} - {value_dict.get('fr', '')} - "
            f"{value_dict.get('it', '')} - {value_dict.get('en', '')}"
        )

    # Return empty string for other types
    return ""


def localize_ckan_sub_dict(ckan_dict, lang_code):
    """localize groups orgs and resources"""
    localized_dict = {}
    for k, v in list(ckan_dict.items()):
        py_v = parse_json(v)
        localized_dict[k] = get_localized_value_from_dict(py_v, lang_code)
    return localized_dict


def get_localized_value_from_dict(value, lang_code, default=""):
    """localizes language dict and
    returns value if it is not a language dict"""
    if not isinstance(value, dict):
        return value
    elif not LANGUAGES.issubset(set(value.keys())):
        return value
    desired_lang_value = value.get(lang_code)
    if desired_lang_value:
        return desired_lang_value
    return localize_by_language_order(value, default)


def get_localized_value_from_json(value, lang_code):
    """localizes language dict from json and
    returns value if it is not a language dict"""
    return get_localized_value_from_dict(parse_json(value), lang_code)


def localize_by_language_order(multi_language_field, default=""):
    """localizes language dict if no language is specified"""
    if multi_language_field.get("de"):
        return multi_language_field["de"]
    elif multi_language_field.get("fr"):
        return multi_language_field["fr"]
    elif multi_language_field.get("en"):
        return multi_language_field["en"]
    elif multi_language_field.get("it"):
        return multi_language_field["it"]
    elif multi_language_field.get("rm"):
        # Sometimes we get resources with only Rumantsch titles.
        # Any resources with info in other languages should also have at least
        # one of de/fr/en/it, so there's no reason to handle those here.
        return multi_language_field["rm"]
    else:
        return default


# this function strips characters with accents, cedilla and umlauts to their
# single character-representation to make the resulting words sortable
# See: http://stackoverflow.com/a/518232
def strip_accents(s):
    if type(s) is not str:
        return s
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
