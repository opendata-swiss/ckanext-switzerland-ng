import logging
import os
from collections import OrderedDict

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.lib.plugins import DefaultTranslation
from ckan.model import PACKAGE_NAME_MAX_LENGTH, Package, Session
from ckan.plugins.toolkit import render

import ckanext.switzerland.helpers.backend_helpers as ogdch_backend_helpers
import ckanext.switzerland.helpers.dataset_form_helpers as ogdch_dataset_form_helpers
import ckanext.switzerland.helpers.date_helpers as ogdch_date_helpers
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
import ckanext.switzerland.helpers.frontend_helpers as ogdch_frontend_helpers
import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
import ckanext.switzerland.helpers.plugin_utils as ogdch_plugin_utils
import ckanext.switzerland.helpers.request_utils as ogdch_request_utils
import ckanext.switzerland.helpers.terms_of_use_utils as ogdch_term_utils
import ckanext.switzerland.helpers.validators as ogdch_validators
import ckanext.xloader.interfaces as ix
from ckanext.activity.model import Activity
from ckanext.hierarchy.plugin import HierarchyDisplay
from ckanext.showcase.plugin import ShowcasePlugin
from ckanext.subscribe.plugin import SubscribePlugin
from ckanext.switzerland import logic as ogdch_logic
from ckanext.switzerland.blueprints.organization import org
from ckanext.switzerland.blueprints.perma import perma
from ckanext.switzerland.blueprints.user import user
from ckanext.switzerland.middleware import RobotsHeaderMiddleware

HARVEST_USER = "harvest"
MIGRATION_USER = "migration"

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


@tk.blanket.config_declarations
class OgdchPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITranslation)

    # ITranslation

    def i18n_domain(self):
        return "ckanext-switzerland"

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        # Register WebAssets
        tk.add_resource("assets", "switzerland")

    # IValidators

    def get_validators(self):
        return {
            "multiple_text": ogdch_validators.multiple_text,
            "multiple_text_output": ogdch_validators.multiple_text_output,
            "multilingual_text_output": ogdch_validators.multilingual_text_output,
            "harvest_list_of_dicts": ogdch_validators.harvest_list_of_dicts,
            "ogdch_language": ogdch_validators.ogdch_language,
            "ogdch_license_required": ogdch_validators.ogdch_license_required,
            "ogdch_unique_identifier": ogdch_validators.ogdch_unique_identifier,
            "ogdch_required_in_one_language": ogdch_validators.ogdch_required_in_one_language,
            "ogdch_validate_formfield_publisher": ogdch_validators.ogdch_validate_formfield_publisher,
            "ogdch_validate_formfield_contact_points": ogdch_validators.ogdch_validate_formfield_contact_points,
            "ogdch_validate_formfield_relations": ogdch_validators.ogdch_validate_formfield_relations,
            "ogdch_validate_formfield_qualified_relations": ogdch_validators.ogdch_validate_formfield_qualified_relations,
            "ogdch_validate_temporals": ogdch_validators.ogdch_validate_temporals,
            "ogdch_fluent_tags": ogdch_validators.ogdch_fluent_tags,
            "ogdch_temp_scheming_choices": ogdch_validators.ogdch_temp_scheming_choices,
            "ogdch_validate_list_of_urls": ogdch_validators.ogdch_validate_list_of_urls,
            "ogdch_validate_list_of_uris": ogdch_validators.ogdch_validate_list_of_uris,
            "ogdch_validate_duration_type": ogdch_validators.ogdch_validate_duration_type,
            "ignore_missing": ogdch_validators.ignore_missing,
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = tk.request.environ["CKAN_LANG"]
        facets_dict = OrderedDict()
        facets_dict["linked_data"] = plugins.toolkit._("Linked Data")
        facets_dict["private"] = plugins.toolkit._("Draft")
        facets_dict["groups"] = plugins.toolkit._("Categories")
        facets_dict[f"keywords_{lang_code}"] = plugins.toolkit._("Keywords")
        facets_dict["organization"] = plugins.toolkit._("Organizations")
        facets_dict["political_level"] = plugins.toolkit._("Political levels")
        facets_dict["res_license"] = plugins.toolkit._("Terms of use")
        facets_dict["res_format"] = plugins.toolkit._("Formats")
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        lang_code = tk.request.environ["CKAN_LANG"]
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict["private"] = plugins.toolkit._("Draft")
        facets_dict[f"keywords_{lang_code}"] = plugins.toolkit._("Keywords")
        facets_dict["organization"] = plugins.toolkit._("Organizations")
        facets_dict["political_level"] = plugins.toolkit._("Political levels")
        facets_dict["res_license"] = plugins.toolkit._("Terms of use")
        facets_dict["res_format"] = plugins.toolkit._("Formats")
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        lang_code = tk.request.environ["CKAN_LANG"]
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict["private"] = plugins.toolkit._("Draft")
        facets_dict["groups"] = plugins.toolkit._("Categories")
        facets_dict[f"keywords_{lang_code}"] = plugins.toolkit._("Keywords")
        facets_dict["res_license"] = plugins.toolkit._("Terms of use")
        facets_dict["res_format"] = plugins.toolkit._("Formats")
        return facets_dict

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            "ogdch_counts": ogdch_logic.ogdch_counts,
            "ogdch_dataset_terms_of_use": ogdch_logic.ogdch_dataset_terms_of_use,
            "ogdch_dataset_by_identifier": ogdch_logic.ogdch_dataset_by_identifier,
            "ogdch_dataset_by_permalink": ogdch_logic.ogdch_dataset_by_permalink,
            "ogdch_content_headers": ogdch_logic.ogdch_content_headers,
            "ogdch_autosuggest": ogdch_logic.ogdch_autosuggest,
            "ogdch_package_show": ogdch_logic.ogdch_package_show,
            "ogdch_xml_upload": ogdch_logic.ogdch_xml_upload,
            "ogdch_showcase_search": ogdch_logic.ogdch_showcase_search,
            "ogdch_add_users_to_groups": ogdch_logic.ogdch_add_users_to_groups,
            "user_create": ogdch_logic.ogdch_user_create,
            "ogdch_harvest_monitor": ogdch_logic.ogdch_harvest_monitor,
            "ogdch_showcase_submit": ogdch_logic.ogdch_showcase_submit,
            "ogdch_subscribe_manage": ogdch_logic.ogdch_subscribe_manage,
            "ogdch_subscribe_unsubscribe": ogdch_logic.ogdch_subscribe_unsubscribe,
            "ogdch_subscribe_unsubscribe_all": ogdch_logic.ogdch_subscribe_unsubscribe_all,
            "ogdch_force_reset_passwords": ogdch_logic.ogdch_force_reset_passwords,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
        return {
            "get_group_count": ogdch_frontend_helpers.get_group_count,
            "get_localized_org": ogdch_frontend_helpers.get_localized_org,
            "localize_json_facet_title": ogdch_frontend_helpers.localize_json_facet_title,
            "localize_harvester_facet_title": ogdch_backend_helpers.localize_harvester_facet_title,
            "localize_showcase_facet_title": ogdch_backend_helpers.localize_showcase_facet_title,
            "get_frequency_name": ogdch_frontend_helpers.get_frequency_name,
            "get_political_level": ogdch_frontend_helpers.get_political_level,
            "get_dataset_terms_of_use": ogdch_term_utils.get_dataset_terms_of_use,
            "get_dataset_by_identifier": ogdch_frontend_helpers.get_dataset_by_identifier,
            "get_dataset_by_permalink": ogdch_frontend_helpers.get_dataset_by_permalink,
            "get_readable_file_size": ogdch_frontend_helpers.get_readable_file_size,
            "ogdch_localised_number": ogdch_frontend_helpers.ogdch_localised_number,
            "ogdch_render_tree": ogdch_frontend_helpers.ogdch_render_tree,
            "ogdch_group_tree": ogdch_frontend_helpers.ogdch_group_tree,
            "get_localized_newsletter_url": ogdch_frontend_helpers.get_localized_newsletter_url,
            "get_localized_date": ogdch_date_helpers.get_localized_date,
            "get_date_picker_format": ogdch_date_helpers.get_date_picker_format,
            "ogdch_template_helper_get_active_class": ogdch_backend_helpers.ogdch_template_helper_get_active_class,
            "ogdch_get_organization_field_list": ogdch_backend_helpers.ogdch_get_organization_field_list,
            "ogdch_get_political_level_field_list": ogdch_backend_helpers.ogdch_get_political_level_field_list,
            "get_localized_value_from_json": ogdch_localize_utils.get_localized_value_from_json,
            "get_localized_value_for_display": ogdch_frontend_helpers.get_localized_value_for_display,
            "ogdch_get_accrual_periodicity_choices": ogdch_dataset_form_helpers.ogdch_get_accrual_periodicity_choices,
            "ogdch_get_license_choices": ogdch_dataset_form_helpers.ogdch_get_license_choices,
            "ogdch_publisher_form_helper": ogdch_dataset_form_helpers.ogdch_publisher_form_helper,
            "ogdch_contact_points_form_helper": ogdch_dataset_form_helpers.ogdch_contact_points_form_helper,
            "ogdch_relations_form_helper": ogdch_dataset_form_helpers.ogdch_relations_form_helper,
            "ogdch_qualified_relations_form_helper": ogdch_dataset_form_helpers.ogdch_qualified_relations_form_helper,
            "ogdch_date_form_helper": ogdch_dataset_form_helpers.ogdch_date_form_helper,
            "ogdch_temporals_form_helper": ogdch_dataset_form_helpers.ogdch_temporals_form_helper,
            "ogdch_dataset_title_form_helper": ogdch_dataset_form_helpers.ogdch_dataset_title_form_helper,
            "ogdch_get_top_level_organisations": ogdch_backend_helpers.ogdch_get_top_level_organisations,
            "ogdch_user_datasets": ogdch_backend_helpers.ogdch_user_datasets,
            # monkey patch template helpers to return translated names/titles
            "resource_display_name": ogdch_backend_helpers.ogdch_resource_display_name,
            "dataset_display_name": ogdch_backend_helpers.dataset_display_name,
            "group_link": ogdch_backend_helpers.group_link,
            "resource_link": ogdch_backend_helpers.resource_link,
            "organization_link": ogdch_backend_helpers.organization_link,
            "ogdch_localize_activity_item": ogdch_backend_helpers.ogdch_localize_activity_item,
            "ogdch_admin_capacity": ogdch_backend_helpers.ogdch_admin_capacity,
            "render_publisher": ogdch_frontend_helpers.render_publisher,
            "ogdch_get_switch_connectome_url": ogdch_backend_helpers.ogdch_get_switch_connectome_url,
            "ogdch_get_env": ogdch_backend_helpers.ogdch_get_env,
            "ogdch_multiple_text_form_helper": ogdch_dataset_form_helpers.ogdch_multiple_text_form_helper,
            "debug_facets": ogdch_frontend_helpers.debug_facets,
        }

    # IBlueprint

    def get_blueprint(self):
        return [org, perma, user]


class OgdchGroupPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IGroupController, inherit=True)

    def before_view(self, grp_dict):
        """
        Transform grp_dict before view.

        This method is not called before requests to CKAN's default API (e.g.
        group_show). It is called in the course of our ogdch_package_show API,
        and in that case, the data is not localized.
        """
        grp_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=grp_dict)
        grp_dict["display_name"] = grp_dict["title"]

        if ogdch_request_utils.request_is_api_request():
            return grp_dict

        request_lang = ogdch_request_utils.get_current_language()
        grp_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=grp_dict, lang_code=request_lang
        )
        return grp_dict

    def edit(self, grp_dict):
        """
        add all CKAN-users as members to the edited group.
        :param grp_dict:
        :return:
        """
        ogdch_logic.ogdch_add_users_to_groups(None, {})


class OgdchOrganizationPlugin(HierarchyDisplay):
    """Implements IOrganizationController to localize organization dictionary in
    before_view.

    Inherits from HierarchyDisplay plugin to make sure that searches for datasets in an
    organization always include datasets belonging to its child organizations as well.
    """

    plugins.implements(plugins.IOrganizationController, inherit=True)

    # IOrganizationController

    def before_view(self, org_dict):
        """
        Transform org_dict before view.

        This method is not called before requests to CKAN's default API (e.g.
        organization_show). It is called in the course of our
        ogdch_package_show API, and in that case, the data is not localized.
        """
        org_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=org_dict)
        org_dict["display_name"] = org_dict["title"]

        if ogdch_request_utils.request_is_api_request():
            return org_dict

        request_lang = ogdch_request_utils.get_current_language()
        org_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=org_dict, lang_code=request_lang
        )
        return org_dict

    # ITemplateHelpers (implemented in parent class HierarchyDisplay)

    def get_helpers(self):
        helpers = super().get_helpers()
        helpers["is_include_children_selected"] = (
            ogdch_backend_helpers.ogdch_is_include_children_selected
        )

        return helpers

    # IPackageController (implemented in parent class HierarchyDisplay)

    def before_dataset_search(self, search_params):
        # Check if we're called from the organization controller, as detected
        # by g being registered for this thread, and the existence of g.group_dict
        try:
            if not hasattr(tk.g, "group_dict"):
                return search_params
        except (TypeError, AttributeError, RuntimeError):
            # it's non-organization controller or CLI call
            return search_params

        # Add special term to the query to tell parent method that we want to include
        # child organizations in the search
        query = search_params.get("q", "")
        query += ' include_children: "True"'
        search_params["q"] = query

        return super().before_dataset_search(search_params)


class OgdchResourcePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController
    def before_resource_show(self, res_dict):
        """
        Transform res_dict before view.

        This method is not called before requests to CKAN's default API (e.g.
        resource_show). It is called in the course of our ogdch_package_show
        API, and in that case, the data is not localized.
        """
        res_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=res_dict)
        res_dict["display_name"] = res_dict["title"]
        res_dict = ogdch_format_utils.prepare_resource_format(resource=res_dict)

        if ogdch_request_utils.request_is_api_request():
            return res_dict

        request_lang = ogdch_request_utils.get_current_language()
        res_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=res_dict, lang_code=request_lang
        )
        return res_dict


class OgdchPackagePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(ix.IXloader, inherit=True)

    # IPackageController

    def before_dataset_view(self, pkg_dict):
        """
        Transform pkg_dict before view.

        This method is not called before requests to CKAN's default API (e.g.
        package_show). It is called in the course of our ogdch_package_show
        API, and in that case, the data is not localized.
        """
        pkg_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=pkg_dict)
        pkg_dict = ogdch_plugin_utils.package_map_ckan_default_fields(pkg_dict)
        pkg_dict["resources"] = [
            ogdch_format_utils.prepare_resource_format(resource=resource)
            for resource in pkg_dict.get("resources")
        ]
        ogdch_plugin_utils.ogdch_map_resource_docs_to_dataset(pkg_dict)

        if ogdch_request_utils.request_is_api_request():
            return pkg_dict

        request_lang = ogdch_request_utils.get_current_language()

        pkg_dict = ogdch_localize_utils.localize_ckan_sub_dict(pkg_dict, request_lang)
        pkg_dict["resources"] = [
            ogdch_localize_utils.localize_ckan_sub_dict(
                ckan_dict=resource, lang_code=request_lang
            )
            for resource in pkg_dict.get("resources")
        ]
        pkg_dict["groups"] = [
            ogdch_localize_utils.localize_ckan_sub_dict(
                ckan_dict=grp, lang_code=request_lang
            )
            for grp in pkg_dict.get("groups")
        ]
        if pkg_dict.get("organization"):
            pkg_dict["organization"] = ogdch_localize_utils.localize_ckan_sub_dict(
                ckan_dict=pkg_dict["organization"], lang_code=request_lang
            )
        return pkg_dict

    def after_dataset_show(self, context, pkg_dict):
        """
        before_view isn't called in API requests -> after_show is
        BUT (!) after_show is also called when packages get indexed
        and there we need all languages.
        -> find a solution to _prepare_package_json() in an API call.
        """
        pkg_dict = ogdch_plugin_utils.ogdch_prepare_pkg_dict_for_api(pkg_dict)
        return pkg_dict

    def before_dataset_index(self, search_data):
        """
        Search data before index
        """
        search_data = ogdch_plugin_utils.ogdch_prepare_search_data_for_index(
            search_data=search_data
        )
        return search_data

    def before_dataset_search(self, search_params):
        """
        Adjust search parameters
        """
        search_params = ogdch_plugin_utils.ogdch_adjust_search_params(search_params)
        return search_params

    # IXloader

    def after_upload(self, context, resource_dict, dataset_dict):
        # create resource views after a successful upload to the DataStore
        tk.get_action("resource_create_default_resource_views")(
            context,
            {
                "resource": resource_dict,
                "package": dataset_dict,
            },
        )


class OgdchArchivePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def delete(self, entity):
        """
        If a package is being deleted it is saved in the CKAN-trash with
        the prefix "_archived-" so that the slug remains available.
        This prevents future datasets with the same name will not have a
        number appended.

        The method is a ckan interface that is called with a lot of different
        instances: we need to make sure that the right cases are picked up:
        datasets that are deleted, but only if they are not already archived.
        In this cases a new name for archiving the dataset is derived.
        """
        if not isinstance(entity, Package):
            return

        if getattr(entity, "state", None) != "deleted":
            return

        if getattr(entity, "type", None) != "dataset":
            return

        dataset_name = getattr(entity, "name", "")
        if dataset_name.startswith("_archived-"):
            return

        entity.name = self._ensure_name_is_unique(f"_archived-{dataset_name}")
        log.info(
            f"Archived dataset name changed to '{entity.name}' (was '{dataset_name}')"
        )

    @staticmethod
    def _ensure_name_is_unique(ideal_name):
        """
        Returns a dataset name based on the ideal_name, only it will be
        guaranteed to be different than all the other datasets, by adding a
        number on the end if necessary.
        The maximum dataset name length is taken account of.
        :param ideal_name: the desired name for the dataset, if its not already
                           been taken (usually derived by munging the dataset
                           title)
        :type ideal_name: string
        """
        ideal_name = ideal_name[:PACKAGE_NAME_MAX_LENGTH]

        MAX_NUMBER_APPENDED = 999
        APPEND_MAX_CHARS = len(str(MAX_NUMBER_APPENDED))
        # Find out which package names have been taken. Restrict it to names
        # derived from the ideal name plus and numbers added
        like_q = f"{ideal_name[:PACKAGE_NAME_MAX_LENGTH - APPEND_MAX_CHARS]}%"
        name_results = (
            Session.query(Package.name).filter(Package.name.ilike(like_q)).all()
        )
        taken = set([name_result[0] for name_result in name_results])
        if ideal_name not in taken:
            # great, the ideal name is available
            return ideal_name
        else:
            # find the next available number
            counter = 1
            while counter <= MAX_NUMBER_APPENDED:
                candidate_name = ideal_name[
                    : PACKAGE_NAME_MAX_LENGTH - len(str(counter))
                ] + str(counter)
                if candidate_name not in taken:
                    return candidate_name
                counter = counter + 1
            return None


class OgdchShowcasePlugin(ShowcasePlugin):
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)

    # IDatasetForm

    def _modify_package_schema(self, schema):
        schema.update(
            {
                "showcase_type": [
                    tk.get_validator("ignore_missing"),
                    tk.get_converter("convert_to_extras"),
                ],
                "private": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("boolean_validator"),
                ],
                "author": [
                    tk.get_validator("convert_to_extras"),
                    tk.get_validator("not_empty"),
                ],
                "author_email": [
                    tk.get_validator("convert_to_extras"),
                    tk.get_validator("not_empty"),
                ],
                "author_twitter": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("convert_to_extras"),
                ],
                "author_github": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("convert_to_extras"),
                ],
                "groups": {
                    "id": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "name": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "title": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "display_name": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                },
            }
        )
        return schema

    def create_package_schema(self):
        schema = super(OgdchShowcasePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(OgdchShowcasePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(OgdchShowcasePlugin, self).show_package_schema()
        schema.update(
            {
                "tracking_summary": [tk.get_validator("ignore_missing")],
                "showcase_type": [
                    tk.get_converter("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ],
                "private": [
                    tk.get_validator("ignore_missing"),
                    tk.get_validator("boolean_validator"),
                ],
                "author": [
                    tk.get_validator("convert_from_extras"),
                    tk.get_validator("not_empty"),
                ],
                "author_email": [
                    tk.get_validator("convert_from_extras"),
                    tk.get_validator("not_empty"),
                ],
                "author_twitter": [
                    tk.get_validator("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ],
                "author_github": [
                    tk.get_validator("convert_from_extras"),
                    tk.get_validator("ignore_missing"),
                ],
                "groups": {
                    "id": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "name": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "title": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                    "display_name": [
                        tk.get_validator("ignore_missing"),
                        tk.get_validator("unicode_safe"),
                    ],
                },
            }
        )
        return schema

    # ITemplateHelpers

    def get_helpers(self):
        helpers = super(OgdchShowcasePlugin, self).get_helpers()
        helpers["showcase_types"] = ogdch_backend_helpers.showcase_types
        helpers["get_showcase_type_name"] = ogdch_backend_helpers.get_showcase_type_name
        helpers["get_localized_group_list"] = (
            ogdch_backend_helpers.get_localized_group_list
        )
        helpers["group_id_in_groups"] = ogdch_backend_helpers.group_id_in_groups

        return helpers

    # IAction
    def get_actions(self):
        """overwrite showcase create logic"""
        action_functions = super(OgdchShowcasePlugin, self).get_actions()
        action_functions["ckanext_showcase_create"] = ogdch_logic.ogdch_showcase_create
        return action_functions

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        if package_type != "showcase":
            return facets_dict

        return OrderedDict(
            {
                "groups": tk._("Categories"),
                "showcase_type": tk._("Type of content"),
                "private": tk._("Draft"),
            }
        )


class OgdchSubscribePlugin(SubscribePlugin):

    # ISubscribe
    def get_email_vars(self, code, subscription=None, email=None, email_vars=None):
        links = [
            "unsubscribe_all_link",
            "manage_link",
            "object_link",
            "unsubscribe_link",
        ]
        email_vars = super(OgdchSubscribePlugin, self).get_email_vars(
            code, subscription, email, email_vars
        )

        ogdch_plugin_utils.ogdch_transform_links(email_vars, links)

        for lang in ogdch_localize_utils.LANGUAGES:
            email_vars[f"object_title_{lang}"] = (
                ogdch_localize_utils.get_localized_value_from_json(
                    email_vars.get("object_title"), lang
                )
            )

        email_vars = {k: str(v) for k, v in list(email_vars.items())}

        return email_vars

    def get_footer_contents(
        self, email_vars, subscription=None, plain_text_footer=None, html_footer=None
    ):
        # Because we are sending emails in four languages, the footers are
        # included in the email templates, not generated separately.
        return "", ""

    def get_manage_email_contents(
        self, email_vars, subject=None, plain_text_body=None, html_body=None
    ):
        subject = "Manage {site_title} subscription".format(**email_vars)

        html_body = render("/emails/subscribe_manage.html", email_vars)
        plain_text_body = render("/emails/subscribe_manage_plain_text.txt", email_vars)

        return subject, plain_text_body, html_body

    def get_subscription_confirmation_email_contents(
        self, email_vars, subject=None, plain_text_body=None, html_body=None
    ):
        subject = (
            "Bestätigungsmail – Confirmation - E-mail di conferma - "
            "Confirmation".format(**email_vars)
        )

        html_body = render("/emails/subscribe_confirmation.html", email_vars)
        plain_text_body = render(
            "/emails/subscribe_confirmation_plain_text.txt", email_vars
        )

        return subject, plain_text_body, html_body

    def get_notification_email_contents(
        self,
        email_vars,
        type="notification",
        subject=None,
        plain_text_body=None,
        html_body=None,
    ):
        # email_vars['notifications'] is a list of dicts of variables, one for
        # each notification in the email.
        # See ckanext.subscribe.notification_email.get_notification_email_vars
        # for the full structure. Our email text only includes links to the
        # datasets that have been updated, so we can ignore the activity
        # links.
        for notification in email_vars.get("notifications"):
            ogdch_plugin_utils.ogdch_transform_links(notification, ["object_link"])

            package_id = notification["activities"][0]["dataset_id"]
            contact_points = ogdch_backend_helpers.get_contact_point_for_dataset(
                package_id
            )

            for lang in ogdch_localize_utils.LANGUAGES:
                notification[f"object_title_{lang}"] = (
                    ogdch_localize_utils.get_localized_value_from_json(
                        notification.get("object_title"), lang
                    )
                )
                notification[f"contact_point_{lang}"] = (
                    ogdch_localize_utils.get_localized_value_from_json(
                        contact_points, lang
                    )
                )

        if type == "deletion":
            subject = (
                "Delete notification – "
                "deleted dataset "
                "{site_title}".format(**email_vars)
            )

            html_body = render("/emails/subscribe_deletion.html", email_vars)
            plain_text_body = render(
                "/emails/subscribe_deletion_plain_text.txt", email_vars
            )
        else:
            subject = (
                "Update notification – "
                "updated dataset "
                "{site_title}".format(**email_vars)
            )

            html_body = render("/emails/subscribe_notification.html", email_vars)
            plain_text_body = render(
                "/emails/subscribe_notification_plain_text.txt", email_vars
            )

        return subject, plain_text_body, html_body

    def get_verification_email_contents(
        self, email_vars, subject=None, plain_text_body=None, html_body=None
    ):
        # These two links are added to the email_vars dict in
        # ckanext-subscribe, separately from the other email_vars. We have to
        # make sure they're unicode strings and point to the frontend.
        ogdch_plugin_utils.ogdch_transform_links(
            email_vars, ["verification_link", "manage_link"]
        )

        subject = (
            "Bestätigungsmail – Confirmation - E-mail di conferma - "
            "Confirmation".format(**email_vars)
        )

        html_body = render("/emails/subscribe_verification.html", email_vars)
        plain_text_body = render(
            "/emails/subscribe_verification_plain_text.txt", email_vars
        )

        return subject, plain_text_body, html_body

    def get_activities(self, include_activity_from, objects_subscribed_to_keys):
        no_notification_users = [HARVEST_USER, MIGRATION_USER]
        query = (
            Session.query(Activity)
            .filter(Activity.timestamp > include_activity_from)
            .filter(Activity.object_id.in_(objects_subscribed_to_keys))
        )
        try:
            for username in no_notification_users:
                user = tk.get_action("user_show")(
                    {"ignore_auth": True}, {"id": username}
                )
                query = query.filter(Activity.user_id != user["id"])
        except tk.ObjectNotFound:
            raise
        activities = query.all()
        return activities


class OgdchMiddlewarePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware)

    def make_middleware(self, app, config):
        app = RobotsHeaderMiddleware(app)

        return app

    def make_error_log_middleware(self, app, config):
        return app
