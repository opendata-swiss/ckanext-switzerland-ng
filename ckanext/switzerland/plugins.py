# coding=UTF-8

from ckan.common import OrderedDict
from ckanext.showcase.plugin import ShowcasePlugin
import ckanext.switzerland.helpers.validators as ogdch_validators
from ckanext.switzerland import logic as ogdch_logic
import ckanext.switzerland.helpers.frontend_helpers as ogdch_frontend_helpers
import ckanext.switzerland.helpers.backend_helpers as ogdch_backend_helpers
import ckanext.switzerland.helpers.dataset_form_helpers as ogdch_dataset_form_helpers  # noqa
import ckanext.switzerland.helpers.plugin_utils as ogdch_plugin_utils
import ckanext.switzerland.helpers.request_utils as ogdch_request_utils
import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
import ckan.plugins as plugins
from ckan.lib.plugins import DefaultTranslation
import ckanext.xloader.interfaces as ix
import ckan.plugins.toolkit as toolkit
import collections
import os
import logging
log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class OgdchPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IRoutes, inherit=True)

    # ITranslation

    def i18n_domain(self):
        return 'ckanext-switzerland'

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'switzerland')

    # IValidators

    def get_validators(self):
        return {
            'multiple_text': ogdch_validators.multiple_text,
            'multiple_text_output': ogdch_validators.multiple_text_output,
            'multilingual_text_output': ogdch_validators.multilingual_text_output, # noqa
            'harvest_list_of_dicts': ogdch_validators.harvest_list_of_dicts,
            'timestamp_to_date_string': ogdch_validators.timestamp_to_date_string, # noqa
            'date_string_to_timestamp': ogdch_validators.date_string_to_timestamp, # noqa
            'ogdch_language': ogdch_validators.ogdch_language,
            'ogdch_unique_identifier': ogdch_validators.ogdch_unique_identifier, # noqa
            'ogdch_required_in_one_language': ogdch_validators.ogdch_required_in_one_language, # noqa
            'temporals_to_datetime_output': ogdch_validators.temporals_to_datetime_output, # noqa
            'ogdch_validate_formfield_publishers': ogdch_validators.ogdch_validate_formfield_publishers,  # noqa
            'ogdch_validate_formfield_contact_points': ogdch_validators.ogdch_validate_formfield_contact_points,  # noqa
            'ogdch_validate_formfield_relations': ogdch_validators.ogdch_validate_formfield_relations,  # noqa
            'ogdch_validate_formfield_see_alsos': ogdch_validators.ogdch_validate_formfield_see_alsos,  # noqa
            'ogdch_validate_formfield_temporals': ogdch_validators.ogdch_validate_formfield_temporals,  # noqa
            'ogdch_fluent_tags': ogdch_validators.ogdch_fluent_tags,
            'ogdch_temp_scheming_choices': ogdch_validators.ogdch_temp_scheming_choices,  # noqa
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['private'] = plugins.toolkit._('Draft')
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['private'] = plugins.toolkit._('Draft')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['private'] = plugins.toolkit._('Draft')
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            'ogdch_counts': ogdch_logic.ogdch_counts,
            'ogdch_dataset_terms_of_use': ogdch_logic.ogdch_dataset_terms_of_use, # noqa
            'ogdch_dataset_by_identifier': ogdch_logic.ogdch_dataset_by_identifier, # noqa
            'ogdch_content_headers': ogdch_logic.ogdch_content_headers,
            'ogdch_autosuggest': ogdch_logic.ogdch_autosuggest,
            'ogdch_package_show': ogdch_logic.ogdch_package_show,
            'ogdch_xml_upload': ogdch_logic.ogdch_xml_upload,
            'ogdch_showcase_search': ogdch_logic.ogdch_showcase_search,
            'ogdch_add_users_to_groups': ogdch_logic.ogdch_add_users_to_groups,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
        return {
            'get_group_count': ogdch_frontend_helpers.get_group_count,
            'get_localized_org': ogdch_frontend_helpers.get_localized_org,
            'localize_json_facet_title': ogdch_frontend_helpers.localize_json_facet_title, # noqa
            'localize_harvester_facet_title': ogdch_backend_helpers.localize_harvester_facet_title, # noqa
            'localize_showcase_facet_title': ogdch_backend_helpers.localize_showcase_facet_title, # noqa
            'get_frequency_name': ogdch_frontend_helpers.get_frequency_name,
            'get_political_level': ogdch_frontend_helpers.get_political_level,
            'get_terms_of_use_icon': ogdch_frontend_helpers.get_terms_of_use_icon, # noqa
            'get_dataset_terms_of_use': ogdch_frontend_helpers.get_dataset_terms_of_use, # noqa
            'get_dataset_by_identifier': ogdch_frontend_helpers.get_dataset_by_identifier, # noqa
            'get_readable_file_size': ogdch_frontend_helpers.get_readable_file_size, # noqa
            'get_piwik_config': ogdch_frontend_helpers.get_piwik_config,
            'ogdch_localised_number': ogdch_frontend_helpers.ogdch_localised_number, # noqa
            'ogdch_render_tree': ogdch_frontend_helpers.ogdch_render_tree,
            'ogdch_group_tree': ogdch_frontend_helpers.ogdch_group_tree,
            'get_terms_of_use_url': ogdch_frontend_helpers.get_terms_of_use_url, # noqa
            'get_localized_newsletter_url': ogdch_frontend_helpers.get_localized_newsletter_url, # noqa
            'get_localized_date': ogdch_frontend_helpers.get_localized_date,
            'ogdch_template_helper_get_active_class': ogdch_backend_helpers.ogdch_template_helper_get_active_class, # noqa
            'ogdch_get_organization_field_list': ogdch_backend_helpers.ogdch_get_organization_field_list, # noqa
            'ogdch_get_political_level_field_list': ogdch_backend_helpers.ogdch_get_political_level_field_list, # noqa
            'get_localized_value_from_json': ogdch_localize_utils.get_localized_value_from_json, # noqa
            'get_localized_value_for_display': ogdch_frontend_helpers.get_localized_value_for_display,  # noqa
            'ogdch_get_accrual_periodicity_choices': ogdch_dataset_form_helpers.ogdch_get_accrual_periodicity_choices,  # noqa
            'ogdch_get_rights_choices': ogdch_dataset_form_helpers.ogdch_get_rights_choices,  # noqa
            'ogdch_publishers_form_helper': ogdch_dataset_form_helpers.ogdch_publishers_form_helper,  # noqa
            'ogdch_contact_points_form_helper': ogdch_dataset_form_helpers.ogdch_contact_points_form_helper,  # noqa
            'ogdch_relations_form_helper': ogdch_dataset_form_helpers.ogdch_relations_form_helper,  # noqa
            'ogdch_see_alsos_form_helper': ogdch_dataset_form_helpers.ogdch_see_alsos_form_helper,  # noqa
            'ogdch_date_form_helper': ogdch_dataset_form_helpers.ogdch_date_form_helper,  # noqa
            'ogdch_temporals_form_helper': ogdch_dataset_form_helpers.ogdch_temporals_form_helper,  # noqa
            'ogdch_dataset_title_form_helper': ogdch_dataset_form_helpers.ogdch_dataset_title_form_helper,  # noqa
            'ogdch_get_top_level_organisations': ogdch_backend_helpers.ogdch_get_top_level_organisations,  # noqa
            # monkey patch template helpers to return translated names/titles
            'resource_display_name': ogdch_backend_helpers.ogdch_resource_display_name,  # noqa
            'dataset_display_name': ogdch_backend_helpers.dataset_display_name,
            'group_link': ogdch_backend_helpers.group_link,
            'resource_link': ogdch_backend_helpers.resource_link,
            'organization_link': ogdch_backend_helpers.organization_link,
            'ogdch_localize_activity_item': ogdch_backend_helpers.ogdch_localize_activity_item,  # noqa
        }

    # IRouter

    def before_map(self, map):
        """adding custom routes to the ckan mapping"""

        # create perma-link route
        map.connect('perma_redirect', '/perma/{id}',
                    controller='ckanext.switzerland.controllers.perma:OgdchPermaController',  # noqa
                    action='read')

        # group routes
        map.connect('group_new', '/group/new',
                    controller='group', action='new')
        map.connect('group_read', '/group/{id}',
                    controller='ckanext.switzerland.controllers.group:OgdchGroupController', # noqa
                    action='read')
        map.connect('group_edit', '/group/edit/{id}', controller='group', action='edit') # noqa

        map.connect('group_index', '/group',
                    controller='ckanext.switzerland.controllers.group:OgdchGroupController', # noqa
                    action='index')

        # organization routes
        map.connect('organization_index', '/organization',
                    controller='ckanext.switzerland.controllers.organization:OgdchOrganizationController', # noqa
                    action='index')
        map.connect('organization_list', '/user/organizations/{id}',
                    controller='ckanext.switzerland.controllers.organization:OgdchOrganizationController',  # noqa
                    action='list_for_user')
        map.connect('organization_new', '/organization/new', controller='organization', action='new') # noqa
        map.connect('organization_read', '/organization/{id}',
                    controller='ckanext.switzerland.controllers.organization:OgdchOrganizationController', # noqa
                    action='read')
        map.connect('organization_edit', '/organization/edit/{id}',
                    controller='organization', action='edit')
        map.connect('organization_xml_upload',
                    '/organization/xml_upload/{name}',
                    controller='ckanext.switzerland.controllers.organization:OgdchOrganizationController', # noqa
                    action='xml_upload')

        return map


class OgdchMixin(object):
    """
    gets format mapping
    """
    def update_config(self, config):
        self.format_mapping = \
            ogdch_format_utils.ogdch_get_format_mapping()


class OgdchGroupPlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IGroupController, inherit=True)

    def before_view(self, grp_dict):
        """localizes the grp_dict for web requests
        that are not api requests"""
        grp_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=grp_dict) # noqa
        grp_dict['display_name'] = grp_dict['title']
        if ogdch_request_utils.request_is_api_request():
            return grp_dict
        request_lang = ogdch_request_utils.get_request_language()
        grp_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=grp_dict,
            lang_code=request_lang)
        return grp_dict

    def edit(self, grp_dict):
        """
        add all CKAN-users as members to the edited group.
        :param grp_dict:
        :return:
        """
        ogdch_backend_helpers.ogdch_add_users_to_groups(None, None)


class OgdchOrganizationPlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IOrganizationController, inherit=True)

    def before_view(self, org_dict):
        org_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=org_dict) # noqa
        org_dict['display_name'] = org_dict['title']
        if ogdch_request_utils.request_is_api_request():
            return org_dict
        request_lang = ogdch_request_utils.get_request_language()
        org_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=org_dict,
            lang_code=request_lang)
        return org_dict


class OgdchResourcePlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController
    def before_show(self, res_dict):
        res_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=res_dict) # noqa
        res_dict['display_name'] = res_dict['title']
        if ogdch_request_utils.request_is_api_request():
            return res_dict
        request_lang = ogdch_request_utils.get_request_language()
        res_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=res_dict,
            lang_code=request_lang)
        res_dict = ogdch_format_utils.prepare_resource_format(
            resource=res_dict, format_mapping=self.format_mapping)
        return res_dict


class OgdchPackagePlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(ix.IXloader, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        """transform pkg dict before view"""
        pkg_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=pkg_dict) # noqa
        pkg_dict = ogdch_plugin_utils.package_map_ckan_default_fields(pkg_dict) # noqa
        pkg_dict['resources'] = [
            ogdch_format_utils.prepare_resource_format(
                resource=resource,
                format_mapping=self.format_mapping)
            for resource in pkg_dict.get('resources')]

        if ogdch_request_utils.request_is_api_request():
            return pkg_dict

        request_lang = ogdch_request_utils.get_request_language()

        pkg_dict = ogdch_localize_utils.localize_ckan_sub_dict(pkg_dict, request_lang) # noqa
        pkg_dict['resources'] = [
            ogdch_localize_utils.localize_ckan_sub_dict(
                ckan_dict=resource,
                lang_code=request_lang)
            for resource in pkg_dict.get('resources')
        ]
        pkg_dict['groups'] = [
            ogdch_localize_utils.localize_ckan_sub_dict(
                ckan_dict=grp,
                lang_code=request_lang)
            for grp in pkg_dict.get('groups')
        ]
        if pkg_dict.get("organization"):
            pkg_dict['organization'] = ogdch_localize_utils.localize_ckan_sub_dict( # noqa
                ckan_dict=pkg_dict['organization'],
                lang_code=request_lang)
        return pkg_dict

    def after_show(self, context, pkg_dict):
        """
        before_view isn't called in API requests -> after_show is
        BUT (!) after_show is also called when packages get indexed
        and there we need all languages.
        -> find a solution to _prepare_package_json() in an API call.
        """
        pkg_dict = ogdch_plugin_utils.ogdch_prepare_pkg_dict_for_api(pkg_dict) # noqa
        return pkg_dict

    def before_index(self, search_data):
        """
        Search data before index
        """
        search_data = ogdch_plugin_utils.ogdch_prepare_search_data_for_index( # noqa
            search_data=search_data,
            format_mapping=self.format_mapping
        )
        return search_data

    def before_search(self, search_params):
        """
        Adjust search parameters
        """
        search_params = ogdch_plugin_utils.ogdch_adjust_search_params(search_params) # noqa
        return search_params

    # IXloader

    def after_upload(self, context, resource_dict, dataset_dict):
        # create resource views after a successful upload to the DataStore
        toolkit.get_action('resource_create_default_resource_views')(
            context,
            {
                'resource': resource_dict,
                'package': dataset_dict,
            }
        )


class OgdchShowcasePlugin(ShowcasePlugin):
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)

    # IConfigurable

    def configure(self, config):
        super(OgdchShowcasePlugin, self).configure(config)
        # create vocabulary if necessary
        ogdch_backend_helpers.create_showcase_types()

    # IDatasetForm

    def _modify_package_schema(self, schema):
        schema.update(
            {
                "showcase_type": [
                    toolkit.get_validator("ignore_missing"),
                    toolkit.get_converter("convert_to_extras"),
                ],
                "groups": {
                    "id": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "name": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "title": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "display_name": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                }
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
                "showcase_type": [
                    toolkit.get_converter("convert_from_extras"),
                    toolkit.get_validator("ignore_missing"),
                ],
                "groups": {
                    "id": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "name": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "title": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                    "display_name": [
                        toolkit.get_validator("ignore_missing"),
                        toolkit.get_validator("unicode_safe"),
                    ],
                }
            }
        )
        return schema

    # ITemplateHelpers

    def get_helpers(self):
        helpers = super(OgdchShowcasePlugin, self).get_helpers()
        helpers["showcase_types"] = ogdch_backend_helpers.showcase_types
        helpers["get_showcase_type_name"] = \
            ogdch_backend_helpers.get_showcase_type_name
        helpers["get_localized_group_list"] = \
            ogdch_backend_helpers.get_localized_group_list
        helpers["group_id_in_groups"] = \
            ogdch_backend_helpers.group_id_in_groups

        return helpers

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        if package_type != "showcase":
            return facets_dict

        return OrderedDict({
            "groups": toolkit._("Categories"),
            "showcase_type": toolkit._("Type of content")
        })
