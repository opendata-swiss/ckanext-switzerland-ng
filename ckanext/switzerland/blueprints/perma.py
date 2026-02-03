import logging

import ckan.logic as logic
from ckan.plugins.toolkit import _, abort, get_action, redirect_to
from flask import Blueprint

log = logging.getLogger(__name__)

NotFound = logic.NotFound

perma = Blueprint("perma", __name__, url_prefix="/perma")


def read(id):
    """
    This action redirects requests to /perma/{identifier} to
    the corresponding /dataset/{slug} route
    """
    try:
        dataset = get_action("ogdch_dataset_by_identifier")(
            {"for_view": True}, {"identifier": id}
        )
        # redirect to dataset detail page
        return redirect_to("dataset.read", id=dataset["name"])
    except NotFound:
        abort(404, _("Dataset not found"))


perma.add_url_rule("/<id>", view_func=read)
