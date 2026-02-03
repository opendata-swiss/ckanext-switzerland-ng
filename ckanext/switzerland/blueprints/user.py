import ckan.lib.base as base
from ckan.plugins.toolkit import get_action
from flask import Blueprint

user = Blueprint("ogdch_user", __name__, url_prefix="/user")


def list_for_user(id):
    user_dict = get_action("user_show")({}, {"id": id, "include_num_followers": True})

    organizations_available = get_action("organization_list_for_user")(
        {"user": user_dict.get("id")}, {"permission": "read"}
    )

    extra_vars = {
        "user_dict": user_dict,
        "organizations_available": organizations_available,
    }

    return base.render("user/organizations.html", extra_vars=extra_vars)


user.add_url_rule("/organizations/<id>", view_func=list_for_user)
