import logging
from typing import Any

import ckan.lib.base as base
import ckan.logic as logic
from ckan.common import _, current_user, request
from ckan.lib.helpers import Page
from ckan.lib.helpers import helper_functions as h
from ckan.plugins.toolkit import get_action, redirect_to, request
from ckan.types import Context
from ckan.views.group import _get_group_template
from flask import Blueprint

log = logging.getLogger(__name__)

ValidationError = logic.ValidationError
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
check_access = logic.check_access

org = Blueprint(
    "ogdch_organization",
    __name__,
    url_prefix="/organization",
)


def xml_upload(name):
    org = get_action("organization_show")({}, {"id": name})

    if request.files.get("file_upload") != "":
        data_dict = {
            "data": dict(request.files),
            "organization": org["id"],
        }
        get_action("ogdch_xml_upload")({}, data_dict)
    else:
        h.flash_error("Error uploading file: no data received.")

    return redirect_to("organization.read", id=name)


def index() -> str:
    """Copied from ckan.views.group.index to remove pagination on the organization
    index page, as it doesn't work well with the ckanext-hierarchy display.
    """
    extra_vars: dict[str, Any] = {}
    page = h.get_page_number(request.args) or 1
    group_type = "organization"
    is_organization = True

    context: Context = {
        "user": current_user.name,
        "for_view": True,
        "with_private": False,
    }

    try:
        action_name = "organization_list" if is_organization else "group_list"
        check_access(action_name, context)
    except NotAuthorized:
        base.abort(403, _("Not authorized to see this page"))

    q = request.args.get("q", "")
    sort_by = request.args.get("sort")

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if current_user.is_authenticated:
        context["user_id"] = current_user.id
        context["user_is_admin"] = current_user.sysadmin  # type: ignore

    try:
        data_dict_global_results: dict[str, Any] = {
            "all_fields": True,
            "q": q,
            "sort": sort_by,
            "type": group_type or "group",
            "include_dataset_count": True,
            "include_member_count": True,
            "include_extras": True,
        }

        action_name = "organization_list" if is_organization else "group_list"
        global_results = get_action(action_name)(context, data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get("message"):
            msg: Any = e.error_dict["message"]
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = Page([], 0)
        extra_vars["group_type"] = group_type
        return base.render(
            _get_group_template("index_template", group_type), extra_vars
        )

    extra_vars["page"] = Page(
        collection=global_results,
        page=page,
        url=h.pager_url,
        items_per_page=len(global_results),
    )

    extra_vars["page"].items = global_results
    extra_vars["group_type"] = group_type
    return base.render(_get_group_template("index_template", group_type), extra_vars)


org.add_url_rule("/xml_upload/<name>", view_func=xml_upload, methods=["POST"])
org.add_url_rule("/", view_func=index, strict_slashes=False)
