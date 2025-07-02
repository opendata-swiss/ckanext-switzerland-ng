import datetime
import logging
import os.path
import random
import re
import string
import uuid
from collections import OrderedDict

import ckan.lib.helpers as h
import ckan.lib.plugins as lib_plugins
import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as tk
import pysolr
import rdflib
import rdflib.parser
from ckan.lib import mailer
from ckan.lib.munge import munge_title_to_name
from ckan.lib.search.common import make_connection
from ckan.logic import (
    ActionError,
    NotAuthorized,
    NotFound,
    ValidationError,
    check_access,
)
from ckan.logic.action.create import user_create as core_user_create
from ckan.plugins.toolkit import config, get_or_bust, side_effect_free
from rdflib.namespace import RDF, Namespace
from unidecode import unidecode

from ckanext.dcatapchharvest.harvesters import SwissDCATRDFHarvester
from ckanext.dcatapchharvest.profiles import SwissDCATAPProfile
from ckanext.harvest.logic.dictization import harvest_job_dictize
from ckanext.harvest.model import HarvestJob
from ckanext.password_policy.helpers import custom_password_check, get_password_length
from ckanext.subscribe.action import (
    subscribe_list_subscriptions,
    subscribe_unsubscribe,
    subscribe_unsubscribe_all,
)
from ckanext.subscribe.email_auth import authenticate_with_code
from ckanext.switzerland.helpers.backend_helpers import ogdch_get_switch_connectome_url
from ckanext.switzerland.helpers.decorators import ratelimit
from ckanext.switzerland.helpers.logic_helpers import (
    get_dataset_count,
    get_org_count,
    get_showcases_for_dataset,
    map_existing_resources_to_new_dataset,
)
from ckanext.switzerland.helpers.mail_helper import (
    send_registration_email,
    send_showcase_email,
)
from ckanext.switzerland.helpers.request_utils import get_content_headers
from ckanext.switzerland.helpers.terms_of_use_utils import get_dataset_terms_of_use

log = logging.getLogger(__name__)

FORMAT_TURTLE = "ttl"
DATA_IDENTIFIER = "data"
RESULT_IDENTIFIER = "result"
HARVEST_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
HARVEST_STATUS_RUNNING = "Running"

DCAT = Namespace("http://www.w3.org/ns/dcat#")
FIVE_MINUTES = 300


@side_effect_free
def ogdch_counts(context, data_dict):
    """
    Return the following data about our ckan instance:
    - total number of datasets
    - number of datasets per group
    - total number of showcases
    - total number of organisations (including all levels of the hierarchy)
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    req_context = {"user": user["name"]}

    # group_list contains the number of datasets in the 'packages' field
    groups = tk.get_action("group_list")(req_context, {"all_fields": True})
    group_count = OrderedDict()
    for group in groups:
        group_count[group["name"]] = group["package_count"]

    return {
        "total_dataset_count": get_dataset_count("dataset"),
        "showcase_count": get_dataset_count("showcase"),
        "groups": group_count,
        "organization_count": get_org_count(),
    }


@side_effect_free
def ogdch_package_show(context, data_dict):
    """Custom package_show logic that returns a dataset together
    with related datasets, showcases, terms of use and SWITCH Connectome url.
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context.update({"user": user["name"], "for_view": True})
    id = get_or_bust(data_dict, "id")

    result = tk.get_action("package_show")(context, {"id": id})
    if not result:
        raise NotFound

    _map_related_datasets(context, result)

    result["showcases"] = get_showcases_for_dataset(id=id)

    result["terms_of_use"] = tk.get_action("ogdch_dataset_terms_of_use")(
        context, {"id": id}
    )

    for resource in result["resources"]:
        resource_views = tk.get_action("resource_view_list")(
            context, {"id": resource["id"]}
        )
        resource["has_views"] = len(resource_views) > 0

    result["connectome_url"] = ogdch_get_switch_connectome_url(
        result.get("identifier", "")
    )

    return result


def _map_related_datasets(context, result):
    """Collate related datasets from both the see_alsos field and the
    qualified_relations field, and get their name and title for display.

    See_alsos is deprecated since DCAT-AP CH v2, and qualified_relations
    replaces it, but older datasets will still have values for see_alsos.
    """
    related_datasets = []
    if result.get("see_alsos"):
        for item in result.get("see_alsos"):
            try:
                related_dataset = tk.get_action("ogdch_dataset_by_identifier")(
                    context, {"identifier": item.get("dataset_identifier")}
                )
                related_datasets.append(
                    {
                        "title": related_dataset["title"],
                        "name": related_dataset["name"],
                        "dataset_identifier": related_dataset["identifier"],
                    }
                )
            except (ValidationError, NotFound) as e:
                log.info(
                    "Error getting related dataset with identifier %s: %s"
                    % (item.get("dataset_identifier"), e)
                )
                continue
    if result.get("qualified_relations"):
        for item in result.get("qualified_relations"):
            try:
                related_dataset = tk.get_action("ogdch_dataset_by_permalink")(
                    context, {"permalink": item.get("relation")}
                )
                related_datasets.append(
                    {
                        "title": related_dataset["title"],
                        "name": related_dataset["name"],
                        "dataset_identifier": related_dataset["identifier"],
                    }
                )
            except (ValidationError, NotFound) as e:
                log.info(
                    "Error getting related dataset with permalink %s: %s"
                    % (item.get("relation"), e)
                )
                related_datasets.append(
                    {
                        "dataset_identifier": item.get("relation"),
                    }
                )
                continue

    result["related_datasets"] = related_datasets


@side_effect_free
def ogdch_content_headers(context, data_dict):
    """
    Returns some headers of a remote resource
    """
    url = get_or_bust(data_dict, "url")
    response = get_content_headers(url)
    return {
        "status_code": response.status_code,
        "content-length": response.headers.get("content-length", ""),
        "content-type": response.headers.get("content-type", ""),
    }


@side_effect_free
def ogdch_dataset_terms_of_use(context, data_dict):
    """
    Returns the terms of use for the requested dataset.

    By definition the terms of use of a dataset corresponds
    to the least open license statement of all distributions of
    the dataset.
    Important : The property dct:license is now required
    for the terms of use instead of dct:rights
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    req_context = {"user": user["name"]}
    pkg_id = get_or_bust(data_dict, "id")
    pkg = tk.get_action("package_show")(req_context, {"id": pkg_id})

    return {
        "dataset_license": get_dataset_terms_of_use(pkg),
    }


@side_effect_free
def ogdch_dataset_by_identifier(context, data_dict):
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context.update({"user": user["name"]})
    identifier = data_dict.pop("identifier", None)

    if not identifier:
        raise ValidationError({"identifier": ["Missing value"]})

    data_dict["fq"] = f"identifier:{identifier}"
    result = tk.get_action("package_search")(context, data_dict)
    try:
        return result["results"][0]
    except (KeyError, IndexError, TypeError):
        raise NotFound


def ogdch_dataset_by_permalink(context, data_dict):
    permalink = data_dict.pop("permalink", None)
    parts = permalink.split("/perma/")
    if len(parts) == 2:
        return ogdch_dataset_by_identifier(context, {"identifier": parts[1]})

    raise NotFound


@side_effect_free
def ogdch_autosuggest(context, data_dict):
    q = get_or_bust(data_dict, "q")
    lang = get_or_bust(data_dict, "lang")
    fq = data_dict.get("fq", "")

    if fq:
        fq = f"NOT private AND {fq}"
    else:
        fq = "NOT private"

    # parse language from values like de_CH
    if len(lang) > 2:
        lang = lang[:2]

    if lang not in ["en", "it", "de", "fr"]:
        raise ValidationError("lang must be one of [en, it, de, fr]")

    handler = f"/suggest_{lang}"
    suggester = f"ckanSuggester_{lang}"

    solr = make_connection()
    try:
        log.debug(f"Loading suggestions for {q} (lang: {lang}, fq: {fq})")
        results = solr.search(
            "",
            search_handler=handler,
            **{"suggest.q": q, "suggest.count": 10, "suggest.cfq": fq}
        )
        suggestions = list(results.raw_response["suggest"][suggester].values())[0]

        def highlight(term, q):
            if "<b>" in term:
                return term
            clean_q = unidecode(q)
            clean_term = unidecode(term)

            re_q = re.escape(clean_q)
            m = re.search(re_q, clean_term, re.I)
            if m:
                replace_text = term[m.start() : m.end()]
                term = term.replace(replace_text, f"<b>{replace_text}</b>")
            return term

        terms = [
            highlight(suggestion["term"], q)
            for suggestion in suggestions["suggestions"]
        ]
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception(f"Could not load suggestions from solr: {e}")
    raise ActionError("Error retrieving suggestions from solr")


def ogdch_xml_upload(context, data_dict):
    data = data_dict.get("data")
    org_id = data_dict.get("organization")

    # Don't use uploader.get_uploader(), as this will return the S3Uploader.
    # We want to process the file locally and then delete it.
    upload = uploader.Upload("dataset_xml")
    upload.update_data_dict(data, "dataset_xml", "file_upload", "clear_upload")
    upload.upload()
    dataset_filename = data.get("dataset_xml")

    if not dataset_filename:
        h.flash_error("Error uploading file.")
        return

    full_file_path = os.path.join(upload.storage_path, dataset_filename)
    data_rdfgraph = rdflib.ConjunctiveGraph()
    profile = SwissDCATAPProfile(data_rdfgraph)

    try:
        data_rdfgraph.parse(full_file_path, "xml")
    except Exception as e:
        h.flash_error(f"Error parsing the RDF file during dataset import: {e}")
        os.remove(full_file_path)
        return

    for dataset_ref in data_rdfgraph.subjects(RDF.type, DCAT.Dataset):
        dataset_dict = {}
        profile.parse_dataset(dataset_dict, dataset_ref)
        dataset_dict["owner_org"] = org_id

        _create_or_update_dataset(dataset_dict)

    # Clean up the file as we have no further use for it.
    os.remove(full_file_path)


@side_effect_free
def ogdch_showcase_search(context, data_dict):
    """
    Custom package_search logic restricted to showcases, with 'for_view'=True
    so that the ckanext-showcase before_view method is called. This includes
    the number of datasets in each showcase in the output.
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context.update({"user": user["name"], "for_view": True})

    if data_dict["fq"]:
        data_dict["fq"] += " dataset_type:showcase"
    else:
        data_dict.update({"fq": "dataset_type:showcase"})

    result = tk.get_action("package_search")(context, data_dict)
    if result:
        return result
    else:
        raise NotFound


@ratelimit
def ogdch_showcase_submit(context, data_dict):
    """
    Custom logic to create a showcase. Showcases can be submitted
    from the frontend and should be created in one step along with
    all the datasets that are attached to the showcase.
    """
    author_email = data_dict.get("author_email")
    if not author_email:
        raise ValidationError("Missing author_email")
    if context.get("ratelimit_exceeded"):
        raise ValidationError(
            "Rate limit of {} calls per {} exceeded: "
            "for {} there were {} calls in that time intervall".format(
                context["limit_call_count"],
                context["limit_timedelta"],
                author_email,
                context["count_of_calls_per_email"],
            )
        )
    try:
        title = data_dict.get("title")
        if not title:
            raise ValidationError("Missing title value")
        data_dict["name"] = munge_title_to_name(title)
        showcase = tk.get_action("ckanext_showcase_create")(context, data_dict)
        package_association_data_dict = {"showcase_id": showcase["id"]}
        datasets = data_dict.get("datasets")
        if datasets:
            for package_id in datasets:
                package_association_data_dict["package_id"] = package_id
                tk.get_action("ckanext_showcase_package_association_create")(
                    context, package_association_data_dict
                )
        return showcase
    except ValidationError:
        raise


@side_effect_free
def ogdch_harvest_monitor(context, data_dict):
    """Returns the status of the fetch and gather processes.

    If there are still-running harvest jobs that were created more than
    6 hours ago, it is likely that either of those processes has stopped
    and needs to be restarted, so we return result["ok"] = False and a list
    of long-running jobs.
    """

    check_access("harvest_job_list", context, data_dict)
    session = context["session"]
    query = (
        session.query(HarvestJob)
        .filter(HarvestJob.status == HARVEST_STATUS_RUNNING)
        .order_by(HarvestJob.created.desc())
    )

    jobs = query.all()

    now = datetime.datetime.now()
    six_hours = datetime.timedelta(hours=6)
    long_jobs = []
    result = {}

    for job in jobs:
        if now - job.created > six_hours:
            long_jobs.append(job)

    result["ok"] = len(long_jobs) == 0

    context["return_error_summary"] = False
    result["long_running_jobs"] = [
        harvest_job_dictize(job, context) for job in long_jobs
    ]

    return result


def _create_or_update_dataset(dataset):
    context = {}
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context.update({"user": user["name"]})

    harvester = SwissDCATRDFHarvester()
    name = harvester._gen_new_name(dataset.get("title", ""))

    package_plugin = lib_plugins.lookup_package_plugin("dataset")
    data_dict = {
        "identifier": dataset.get("identifier", ""),
        "include_private": True,
        "include_drafts": True,
    }

    try:
        existing_dataset = tk.get_action("ogdch_dataset_by_identifier")(
            context, data_dict
        )
        context["schema"] = package_plugin.update_package_schema()

        # Don't change the dataset name even if the title has changed
        dataset["name"] = existing_dataset["name"]
        dataset["id"] = existing_dataset["id"]
        # Don't make a dataset public if it wasn't already
        is_private = existing_dataset["private"]
        dataset["private"] = is_private

        map_existing_resources_to_new_dataset(dataset, existing_dataset)

        tk.get_action("package_update")(context, dataset)

        success_message = f"Updated dataset {dataset['name']}."
        if is_private:
            success_message += " The dataset visibility is private."

        h.flash_success(success_message)

    except NotFound:
        package_schema = package_plugin.create_package_schema()
        context["schema"] = package_schema

        # We need to explicitly provide a package ID
        dataset["id"] = str(uuid.uuid4())
        package_schema["id"] = [str]
        dataset["name"] = name
        # Create datasets as private initially
        dataset["private"] = True

        try:
            tk.get_action("package_create")(context, dataset)
        except ValidationError as e:
            h.flash_error(
                "Error importing dataset %s: %r"
                % (dataset.get("name", ""), e.error_summary)
            )

            return

        h.flash_success(
            f"Created dataset {dataset['name']}. The dataset visibility is private."
        )

    except Exception as e:
        h.flash_error(f"Error importing dataset {dataset.get('name', '')}: {e}")


@side_effect_free
def ogdch_add_users_to_groups(context, data_dict={}):
    """
    If user_id and group_id is given, that user will be added to that group.
    If only user_id is given, they will be added to each group.
    If only group_id is given, all non-sysadmin users
    will be added as members to that group
    :param user_id: (optional, default: ``None``)
    :param group_id: (optional, default: ``None``)
    :return:
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, ())
    context = {"user": user["name"]}

    group_id = data_dict.get("group_id")
    user_id = data_dict.get("user_id")

    if user_id and group_id:
        _add_member_to_group(user_id, group_id, context)
        return f'Added user "{user_id}" to "{group_id}".'
    elif user_id:
        _add_member_to_groups(user_id, context)
        return f"Added user {user_id} to all available groups."
    elif group_id:
        _add_members_to_group(group_id, context)
        return f"Added all non-admin users as members to group {group_id}."
    else:
        members = tk.get_action("user_list")(context, {})
        groups = tk.get_action("group_list")(context, {})
        for member in members:
            if not member["sysadmin"]:
                for group in groups:
                    _add_member_to_group(member.get("id"), group, context)

        return "Added all non-admin users as members to all available groups."


def _add_members_to_group(group, context):
    members = tk.get_action("user_list")(context, {})
    for member in members:
        if not member["sysadmin"]:
            _add_member_to_group(member.get("id"), group, context)


def _add_member_to_groups(member, context):
    groups = tk.get_action("group_list")(context, {})
    for group in groups:
        _add_member_to_group(member, group, context)


def _add_member_to_group(member, group, context):
    update_group_members_dict = {
        "id": group,
        "username": member,
        "role": "member",
    }
    tk.get_action("group_member_create")(context, update_group_members_dict)


def ogdch_user_create(context, data_dict):
    """overwrites the core user creation to send an email
    to new users"""
    user = core_user_create(context, data_dict)
    tk.get_action("ogdch_add_users_to_groups")(context, {"user_id": user["id"]})
    send_email_on_registration = tk.asbool(
        config.get("ckanext.switzerland.send_email_on_user_registration", True)
    )

    if not (send_email_on_registration and user.get("email")):
        return user

    success = False
    exception = ""
    try:
        send_registration_email(user)
        success = True
    except Exception as e:
        exception = e

    try:
        if success:
            h.flash_success(
                f"An email has been sent to the user {user['name']} at {user['email']}."
            )
        else:
            message = "The email could not be sent to {} for user {}.".format(
                user["email"], user["name"]
            )
            if exception:
                message += f" An error occured: {exception}"
            h.flash_error(message)
    except TypeError:
        # We get this error when creating a user via the command line.
        # Then there is no session, so showing a flash message fails.
        log.warning(
            "The email could not be sent to {} for user {}."
            " An error occured: {}".format(user["email"], user["name"], exception)
        )

    return user


def ogdch_showcase_create(context, data_dict):
    """Custom showcase creation so that a notification
    can be sent when a showcase is created."""
    data_dict["type"] = "showcase"

    upload = uploader.get_uploader("showcase")

    upload.update_data_dict(data_dict, "image_url", "image_upload", "clear_upload")

    upload.upload(uploader.get_max_image_size())

    showcase = tk.get_action("package_create")(context, data_dict)
    try:
        send_showcase_email(showcase)
    except Exception as e:
        log.error(
            "Sending a notification when a showcase was created"
            " received an exception: {}".format(e)
        )
    return showcase


def _get_email_from_subscribe_code(code):
    """Get the email address of a subscription from an auth code."""
    try:
        email = authenticate_with_code(code)
    except ValueError:
        raise ValidationError("Code is not valid")

    if not email:
        raise Exception("The email is not valid")

    return email


def ogdch_subscribe_manage(context, data_dict):
    """Get an email address from a given auth code, and then return
    information about existing subscriptions for that email address.
    :returns: list of dictionaries
    """
    data_dict["email"] = _get_email_from_subscribe_code(data_dict["code"])

    return subscribe_list_subscriptions(context, data_dict)


def ogdch_subscribe_unsubscribe(context, data_dict):
    """Get an email address from a given auth code, and then unsubscribe that
    email address from notifications for a given dataset.

    :returns: (object_name, object_type) where object_type is: dataset, group
        or organization (but we are only offering dataset subscriptions on the
        frontend, so it will be dataset)
    """
    data_dict["email"] = _get_email_from_subscribe_code(data_dict["code"])

    return subscribe_unsubscribe(context, data_dict)


def ogdch_subscribe_unsubscribe_all(context, data_dict):
    """Get an email address from a given auth code, and then unsubscribe
    that email address from all notifications.

    :returns: None
    """
    data_dict["email"] = _get_email_from_subscribe_code(data_dict["code"])

    return subscribe_unsubscribe_all(context, data_dict)


def ogdch_force_reset_passwords(context, data_dict):
    """Reset the password of a single user, or of all users, to a random value
    that fulfills our password requirements. The new password is not
    communicated to the users. If resetting all users, limit and offset values
    are used so that the action won't timeout trying to update every user in
    one call.

    Optionally, email the user(s) a link to reset their passwords again to a
    value of their choosing.

    data_dict params:

    :param user:    a single username to reset the password for (optional)
    :param limit:   if given, the list of users will be broken into pages of
                    at most ``limit`` users per page and only one page will
                    have their passwords reset at a time (optional)
    :type limit:    int
    :param offset:  when ``limit`` is given, the offset to start resetting user
                    passwords from (optional)
    :type limit:    int
    :param notify:  whether to email the user(s) a password-reset link
    :type notify    bool

    :return: a dictionary containing a list of usernames whose passwords were
             successfully reset and any errors encountered
    :rtype: dict
    """
    try:
        check_access("user_delete", context)
    except NotAuthorized:
        raise NotAuthorized("Unauthorized to reset passwords.")

    # Allow specifying single user or all users
    username = data_dict.get("user")
    # If resetting passwords for multiple users, use limit and offset to
    # ensure we won't try to reset everyone and timeout
    limit = int(data_dict.get("limit", 10))
    offset = int(data_dict.get("offset", 0))
    notify = tk.asbool(data_dict.get("notify", True))

    if username:
        usernames = [username]
    else:
        usernames = tk.get_action("user_list")(context, {"all_fields": False})[
            offset : offset + limit
        ]

    results = {
        "success_users": [],
        "errors": {},
    }
    for name in usernames:
        success, error = _reset_password(name, context, notify)
        if success:
            results["success_users"].append(name)
        else:
            results["errors"][name] = error

    return results


def _reset_password(username, context, notify):
    """Reset a user's password to a random value and, optionally, send them
    a link to reset the password again to a value of their choosing.
    """
    auth_user = context.get("auth_user_obj")
    if username == auth_user.name:
        return False, f"Not resetting password for the signed-in user {username}"

    user_dict = tk.get_action("user_show")(context, {"id": username})
    user_obj = context.get("user_obj")
    password = _generate_password(user_dict)

    # First, reset password to a random new value that won't be transmitted
    log.info(f"Resetting password for user: {user_dict['name']}")
    user_dict["password"] = password
    try:
        tk.get_action("user_update")(context, user_dict)
    except ValidationError as e:
        return False, str(e)

    # Then trigger reset email
    if notify:
        log.info(f"Emailing reset link to user: {user_dict['name']}")
        try:
            mailer.send_reset_link(user_obj)
        except mailer.MailerException as e:
            # SMTP is not configured correctly or the server is
            # temporarily unavailable
            return False, str(e)

    return True, None


def _generate_password(user):
    """Generate a password that fits our requirements. Code adapted from ckan
    user_invite action.
    """
    password_length = get_password_length(user["name"])
    while True:
        password = "".join(
            random.SystemRandom().choice(
                string.ascii_lowercase
                + string.ascii_uppercase
                + string.digits
                + string.punctuation
            )
            for _ in range(password_length)
        )
        # Occasionally it won't meet the constraints, so check
        errors = {}
        custom_password_check(
            password=password, username=user["name"], fullname=user["fullname"]
        )
        if not errors:
            break
    return password
