# coding=UTF-8

from ckanext.showcase.plugin import ShowcasePlugin
import ckanext.switzerland.helpers.validators as ogdch_validators
from ckanext.switzerland import logic as ogdch_logic
import ckanext.switzerland.helpers.frontend_helpers as ogdch_frontend_helpers
import ckanext.switzerland.helpers.backend_helpers as ogdch_backend_helpers
import ckanext.switzerland.helpers.plugin_utils as ogdch_plugin_utils
import ckanext.switzerland.helpers.request_utils as ogdch_request_utils
import ckanext.switzerland.helpers.localize_utils as ogdch_localize_utils
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
import re
from webhelpers.html import HTML
from webhelpers import paginate
import ckan.plugins as plugins
from ckan.lib.plugins import DefaultTranslation
import ckanext.xloader.interfaces as ix
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
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

    # IValidators

    def get_validators(self):
        return {
            'multiple_text': ogdch_validators.multiple_text,
            'multiple_text_output': ogdch_validators.multiple_text_output,
            'multilingual_text_output': ogdch_validators.multilingual_text_output,
            'list_of_dicts': ogdch_validators.list_of_dicts,
            'timestamp_to_datetime': ogdch_validators.timestamp_to_datetime,
            'ogdch_language': ogdch_validators.ogdch_language,
            'ogdch_unique_identifier': ogdch_validators.ogdch_unique_identifier,
            'temporals_to_datetime_output': ogdch_validators.temporals_to_datetime_output,
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
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
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            'ogdch_dataset_count': ogdch_logic.ogdch_dataset_count,
            'ogdch_dataset_terms_of_use': ogdch_logic.ogdch_dataset_terms_of_use,
            'ogdch_dataset_by_identifier': ogdch_logic.ogdch_dataset_by_identifier,
            'ogdch_content_headers': ogdch_logic.ogdch_content_headers,
            'ogdch_autosuggest': ogdch_logic.ogdch_autosuggest,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
        return {
            'get_dataset_count': ogdch_frontend_helpers.get_dataset_count,
            'get_group_count': ogdch_frontend_helpers.get_group_count,
            'get_app_count': ogdch_frontend_helpers.get_app_count,
            'get_org_count': ogdch_frontend_helpers.get_org_count,
            'get_localized_org': ogdch_frontend_helpers.get_localized_org,
            'localize_json_title': ogdch_frontend_helpers.localize_json_title,
            'get_frequency_name': ogdch_frontend_helpers.get_frequency_name,
            'get_political_level': ogdch_frontend_helpers.get_political_level,
            'get_terms_of_use_icon': ogdch_frontend_helpers.get_terms_of_use_icon,
            'get_dataset_terms_of_use': ogdch_frontend_helpers.get_dataset_terms_of_use,
            'get_dataset_by_identifier': ogdch_frontend_helpers.get_dataset_by_identifier,
            'get_readable_file_size': ogdch_frontend_helpers.get_readable_file_size,
            'get_piwik_config': ogdch_frontend_helpers.get_piwik_config,
            'ogdch_localised_number': ogdch_frontend_helpers.ogdch_localised_number,
            'ogdch_render_tree': ogdch_frontend_helpers.ogdch_render_tree,
            'ogdch_group_tree': ogdch_frontend_helpers.ogdch_group_tree,
            'get_showcases_for_dataset': ogdch_frontend_helpers.get_showcases_for_dataset,
            'get_terms_of_use_url': ogdch_frontend_helpers.get_terms_of_use_url,
            'get_localized_newsletter_url': ogdch_frontend_helpers.get_localized_newsletter_url,
            'ogdch_template_helper_get_active_class': ogdch_backend_helpers.ogdch_template_helper_get_active_class, # noqa
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
        map.connect('organization_new', '/organization/new', controller='organization', action='new') # noqa
        map.connect('organization_read', '/organization/{id}',
                    controller='ckanext.switzerland.controllers.organization:OgdchOrganizationController', # noqa
                    action='read')
        map.connect('organization_edit', '/organization/edit/{id}',
                    controller='organization', action='edit')

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
        grp_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=grp_dict)
        grp_dict['display_name'] = grp_dict['title']
        if ogdch_request_utils.request_is_api_request():
            return grp_dict
        request_lang = ogdch_request_utils.get_request_language()
        grp_dict = ogdch_localize_utils.localize_ckan_sub_dict(
            ckan_dict=grp_dict,
            lang_code=request_lang)
        return grp_dict


class OgdchOrganizationPlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IOrganizationController, inherit=True)

    def before_view(self, org_dict):
        org_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=org_dict)
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
        res_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=res_dict)
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
        pkg_dict = ogdch_localize_utils.parse_json_attributes(ckan_dict=pkg_dict)
        pkg_dict = ogdch_plugin_utils.package_map_ckan_default_fields(pkg_dict)
        pkg_dict['resources'] = [
            ogdch_format_utils.prepare_resource_format(
                resource=resource,
                format_mapping=self.format_mapping)
            for resource in pkg_dict.get('resources')]

        if ogdch_request_utils.request_is_api_request():
            return pkg_dict

        request_lang = ogdch_request_utils.get_request_language()

        pkg_dict = ogdch_localize_utils.localize_ckan_sub_dict(pkg_dict, request_lang)
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
            pkg_dict['organization'] = ogdch_localize_utils.localize_ckan_sub_dict(
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
        pkg_dict = ogdch_plugin_utils.ogdch_prepare_pkg_dict_for_api(pkg_dict)
        return pkg_dict

    def before_index(self, search_data):
        """
        Search data before index
        """
        search_data = ogdch_plugin_utils.ogdch_prepare_search_data_for_index(
            search_data=search_data,
            format_mapping=self.format_mapping
        )
        return search_data

    def before_search(self, search_params):
        """
        Adjust search parameters
        """
        search_params = ogdch_plugin_utils.ogdch_adjust_search_params(search_params)
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
    pass

