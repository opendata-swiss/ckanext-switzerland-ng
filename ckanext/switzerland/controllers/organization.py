# encoding: utf-8

import logging
from collections import OrderedDict
from urllib import urlencode

import ckan.authz as authz
import ckan.controllers.organization as organization
import ckan.lib.helpers as h
import ckan.lib.search as search
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.lib.base import render
from ckan.lib.plugins import lookup_group_controller
from ckan.logic import NotAuthorized, ValidationError, get_action
from ckan.plugins.toolkit import _, c, config, request

import ckanext.hierarchy.helpers as hierarchy_helpers

log = logging.getLogger(__name__)


def _children_name_list(children):
    name_list = []
    for child in children:
        name = child.get("name", "")
        name_list += [name] + _children_name_list(child.get("children", []))
    return name_list


class OgdchOrganizationController(organization.OrganizationController):

    def _read(self, id, limit, group_type):  # noqa
        """
        This controller replaces the HierarchyOrganizationController controller
        from ckanext-hierarchy. It makes sure, that datasets of
        sub-organizations are included on the organisation detail page and
        uses the filter query (fq) parameter of Solr to limit the search
        instead of the owner_org query used in CKAN core.
        In order to replace HierarchyOrganizationController it's important
        to load the ogdch_org_search plugin _after_ the hierarchy_display
        plugin in the plugin list of the active ini file. Unfortunately
        there are no clean extension points in the OrganizationController,
        so that the _read() method had to be overridden completely.
        """
        c.include_children_selected = False

        if not c.group_dict.get("is_organization"):
            return

        """ This is common code used by both read and bulk_process"""
        context = {
            "model": model,
            "session": model.Session,
            "user": c.user or c.author,
            "schema": self._db_to_form_schema(group_type=group_type),
            "for_view": True,
            "extras_as_string": True,
        }

        c.description_formatted = h.render_markdown(c.group_dict.get("description"))

        context["return_query"] = True

        # c.group_admins is used by CKAN's legacy (Genshi) templates only,
        # if we drop support for those then we can delete this line.
        c.group_admins = authz.get_group_or_org_admin_ids(c.group.id)

        page = h.get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items() if k != "page"]
        sort_by = request.params.get("sort", None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = "bulk_process" if c.action == "bulk_process" else "read"
            url = h.url_for(controller=controller, action=action, id=id)
            params = [
                (k, v.encode("utf-8") if isinstance(v, basestring) else str(v))
                for k, v in params
            ]
            return url + "?" + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(
                alternative_url=None,
                controller="group",
                action="read",
                extras=dict(id=c.group_dict.get("name")),
                new_params=by,
            )

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(
                key,
                value=value,
                replace=replace,
                controller="group",
                action="read",
                extras=dict(id=c.group_dict.get("name")),
            )

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(("page", page))
            return search_url(params)

        try:
            q = c.q = request.params.get("q", "")
            fq = c.fq = request.params.get("fq", "")

            c.fields = []
            search_extras = {}
            for param, value in request.params.items():
                if (
                    param not in ["q", "page", "sort"]
                    and len(value)
                    and not param.startswith("_")
                ):
                    if not param.startswith("ext_"):
                        c.fields.append((param, value))
                        fq += ' %s: "%s"' % (param, value)
                    else:
                        search_extras[param] = value

            user_member_of_orgs = [
                org["id"] for org in h.organizations_available("read")
            ]

            if c.group and c.group.id in user_member_of_orgs:
                context["ignore_capacity_check"] = True
            else:
                fq += ' capacity:"public"'

            facets = OrderedDict()

            default_facet_titles = {
                "organization": _("Organizations"),
                "groups": _("Groups"),
                "tags": _("Tags"),
                "res_format": _("Formats"),
                "license_id": _("Licenses"),
            }

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            if "capacity" in facets and (
                group_type != "organization" or not user_member_of_orgs
            ):
                del facets["capacity"]

            c.facet_titles = facets

            # filter by organization with fq (filter query)
            c.include_children_selected = True
            children = _children_name_list(
                hierarchy_helpers.group_tree_section(
                    c.group_dict.get("id"),
                    include_parents=False,
                    include_siblings=False,
                ).get("children", [])
            )

            if not children:
                fq += ' organization:"%s"' % c.group_dict.get("name")
            else:
                fq += ' organization:("%s"' % c.group_dict.get("name")
                for name in children:
                    if name:
                        fq += ' OR "%s"' % name
                fq += ")"

            data_dict = {
                "q": q,
                "fq": fq,
                "facet.field": facets.keys(),
                "rows": limit,
                "sort": sort_by,
                "start": (page - 1) * limit,
                "extras": search_extras,
                "include_private": True,
            }

            context_ = dict((k, v) for (k, v) in context.items() if k != "schema")
            query = get_action("package_search")(context_, data_dict)

            c.page = h.Page(
                collection=query["results"],
                page=page,
                url=pager_url,
                item_count=query["count"],
                items_per_page=limit,
            )

            c.group_dict["package_count"] = query["count"]

            c.search_facets = query["search_facets"]
            c.search_facets_limits = {}
            for facet in c.search_facets.keys():
                limit = int(
                    request.params.get(
                        "_%s_limit" % facet, config.get("search.facets.default", 10)
                    )
                )
                c.search_facets_limits[facet] = limit
            c.page.items = query["results"]

            c.sort_by_selected = sort_by

        except search.SearchError as se:
            log.error("Group search error: %r", se.args)
            c.query_error = True
            c.search_facets = {}
            c.page = h.Page(collection=[])

        self._setup_template_variables(context, {"id": id}, group_type=group_type)
        return

    """
    Disable pagination on the Organization index page, because it doesn't work
    well with the ckanext-hierarchy display.
    """

    def index(self):
        group_type = self._guess_group_type()

        page = h.get_page_number(request.params) or 1

        context = {
            "model": model,
            "session": model.Session,
            "user": c.user,
            "for_view": True,
            "with_private": False,
        }

        q = c.q = request.params.get("q", "")
        sort_by = c.sort_by_selected = request.params.get("sort")
        try:
            self._check_access("site_read", context)
            self._check_access("group_list", context)
        except NotAuthorized:
            tk.abort(403, _("Not authorized to see this page"))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context["user_id"] = c.userobj.id
            context["user_is_admin"] = c.userobj.sysadmin

        try:
            data_dict_global_results = {
                "all_fields": True,
                "q": q,
                "sort": sort_by,
                "type": group_type or "group",
                "include_extras": True,
                "include_dataset_count": False,
            }
            global_results = self._action("group_list")(
                context, data_dict_global_results
            )
        except ValidationError as e:
            if e.error_dict and e.error_dict.get("message"):
                msg = e.error_dict["message"]
            else:
                msg = str(e)
            h.flash_error(msg)
            c.page = h.Page([], 0)
            return render(
                self._index_template(group_type), extra_vars={"group_type": group_type}
            )

        c.page = h.Page(
            collection=global_results,
            page=page,
            url=h.pager_url,
            items_per_page=len(global_results),
        )

        c.page.items = global_results
        return render(
            self._index_template(group_type),
            extra_vars={"group_type": group_type, "q": request.params.get("q", "")},
        )

    def list_for_user(self, id):
        user_dict = tk.get_action("user_show")(
            {}, {"id": id, "include_num_followers": True}
        )

        organizations_available = tk.get_action("organization_list_for_user")(
            {"user": user_dict.get("id")}, {"permission": "read"}
        )

        extra_vars = {
            "user_dict": user_dict,
            "organizations_available": organizations_available,
        }

        return render("user/organizations.html", extra_vars=extra_vars)

    def xml_upload(self, name):
        if not tk.request.method == "POST":
            tk.abort(409, _("Only POST is available"))

        org = tk.get_action("organization_show")({}, {"id": name})

        if tk.request.POST.get("file_upload") != "":
            data_dict = {
                "data": dict(tk.request.POST),
                "organization": org["id"],
            }
            tk.get_action("ogdch_xml_upload")({}, data_dict)
        else:
            h.flash_error("Error uploading file: no data received.")

        tk.redirect_to("organization_read", id=name)
