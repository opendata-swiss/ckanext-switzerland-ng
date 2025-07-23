import logging

from ckan.lib.helpers import flash_error
from ckan.plugins.toolkit import get_action, redirect_to, request
from flask import Blueprint

log = logging.getLogger(__name__)

org = Blueprint("ogdch_organization", __name__, url_prefix="/organization")


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


org.add_url_rule("/xml_upload/<name>", view_func=xml_upload, methods=["POST"])
