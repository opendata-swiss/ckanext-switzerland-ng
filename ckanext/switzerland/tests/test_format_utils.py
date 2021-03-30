"""Tests for helpers.format_utils.py."""
import ckanext.switzerland.plugins as plugins
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
from nose.tools import *  # noqa
import sys
import os
import yaml

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

class TestPlugin(unittest.TestCase):
    def setUp(self):
        return

    def tearDown(self):
        return

    def _load_test_format_mapping(self):
        with open(os.path.join(__location__, 'test_mapping.yaml'),
                  'r') as format_mapping_file:
            return yaml.safe_load(format_mapping_file)

    def test_prepare_resource_format(self):
        ogdch_mixin = plugins.OgdchMixin()

        ogdch_mixin.format_mapping = self._load_test_format_mapping()

        resource_with_no_format_and_no_download_url = {
            'download_url': None,
            'media_type': None,
            'format': None
        }
        resource_with_no_format_and_no_download_url_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_no_format_and_no_download_url.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('SERVICE', resource_with_no_format_and_no_download_url_cleaned['format'])

        resource_with_invalid_format_and_with_download_url = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'dogvideo'
        }
        resource_with_invalid_format_and_with_download_url_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_invalid_format_and_with_download_url.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('', resource_with_invalid_format_and_with_download_url_cleaned['format'])

        resource_without_any_formats_with_download_url = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': None
        }
        resource_without_any_formats_with_download_url_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_without_any_formats_with_download_url.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('', resource_without_any_formats_with_download_url_cleaned['format'])

        resource_with_invalid_format_and_no_download_url = {
            'download_url': None,
            'media_type': None,
            'format': 'catgif'
        }
        resource_with_invalid_format_and_no_download_url_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_invalid_format_and_no_download_url.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('SERVICE', resource_with_invalid_format_and_no_download_url_cleaned['format'])

        resource_with_valid_format = {
            'download_url': None,
            'media_type': None,
            'format': 'xml'
        }
        resource_with_valid_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_valid_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('XML', resource_with_valid_format_cleaned['format'])

        resource_with_invalid_media_type_but_valid_after_slash = {
            'download_url': 'http://download.url',
            'media_type': 'cat/gif',
            'format': 'gif'
        }
        resource_with_invalid_media_type_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_invalid_media_type_but_valid_after_slash.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('gif', resource_with_invalid_media_type_cleaned['format'])

        resource_with_valid_media_type_without_slash = {
            'download_url': None,
            'media_type': 'html',
            'format': 'xml'
        }
        resource_with_valid_media_type_without_slash_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_valid_media_type_without_slash.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('HTML', resource_with_valid_media_type_without_slash_cleaned['format'])

        resource_with_valid_media_type_with_slash = {
            'download_url': None,
            'media_type': 'text/html',
            'format': 'xml'
        }
        resource_with_valid_media_type_with_slash_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_valid_media_type_with_slash.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('HTML', resource_with_valid_media_type_with_slash_cleaned['format'])

        resourse_with_download_url_without_extension = {
            'download_url': 'http://download.url',
            'media_type': 'text/xml',
            'format': 'html'
        }
        resourse_with_download_url_without_extension_cleaned = ogdch_format_utils.prepare_resource_format(
            resourse_with_download_url_without_extension.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('XML', resourse_with_download_url_without_extension_cleaned['format'])

        resourse_with_download_url_with_invalid_extension = {
            'download_url': 'http://download.url/cat.gif?param=1',
            'media_type': '',
            'format': ''
        }
        resourse_with_download_url_with_invalid_extension_cleaned = ogdch_format_utils.prepare_resource_format(
            resourse_with_download_url_with_invalid_extension.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('', resourse_with_download_url_with_invalid_extension_cleaned['format'])

        resourse_with_download_url_with_invalid_extension_but_format = {
            'download_url': 'http://download.url/cat.gif?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_invalid_extension_but_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resourse_with_download_url_with_invalid_extension_but_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('XML', resourse_with_download_url_with_invalid_extension_but_format_cleaned['format'])

        resourse_with_download_url_with_valid_extension = {
            'download_url': 'http://download.url/file.zip?param=1',
            'media_type': '',
            'format': ''
        }
        resourse_with_download_url_with_valid_extension_cleaned = ogdch_format_utils.prepare_resource_format(
            resourse_with_download_url_with_valid_extension.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('ZIP', resourse_with_download_url_with_valid_extension_cleaned['format'])

        resourse_with_download_url_with_valid_extension_but_format = {
            'download_url': 'http://download.url/file.zip?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_valid_extension_but_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resourse_with_download_url_with_valid_extension_but_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('XML', resourse_with_download_url_with_valid_extension_but_format_cleaned['format'])

        resource_with_ods_vndoas_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'application/vnd.oas...'
        }
        resource_with_ods_vndoas_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_ods_vndoas_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('ODS', resource_with_ods_vndoas_format_cleaned['format'])

        resource_with_vndoxml_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        resource_with_vndoxml_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_vndoxml_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('XLS', resource_with_vndoxml_format_cleaned['format'])

        resource_with_pcaxis_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'pc-axis file'
        }
        resource_with_pcaxis_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_pcaxis_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('PC-AXIS', resource_with_pcaxis_format_cleaned['format'])

        resource_with_pcaxis_format = {
            'download_url': 'http://download.url/Download.aspx?file=pc-axis-file-001',
            'media_type': 'pc-axis file',
            'format': 'CSV'
        }
        resource_with_pcaxis_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_pcaxis_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('PC-AXIS', resource_with_pcaxis_format_cleaned['format'])

        resource_with_rdf_sparql_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'Application/Sparql-...'
        }
        resource_with_rdf_sparql_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_rdf_sparql_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('RDF', resource_with_rdf_sparql_format_cleaned['format'])

        resource_with_shapefile_esri_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'ESRI Shapefile'
        }
        resource_with_shapefile_esri_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_shapefile_esri_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('SHAPEFILE', resource_with_shapefile_esri_format_cleaned['format'])

        resource_with_text_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'text (.txt)'
        }
        resource_with_text_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_text_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('TXT', resource_with_text_format_cleaned['format'])

        resource_with_comma_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'comma ...'
        }
        resource_with_comma_format_cleaned = ogdch_format_utils.prepare_resource_format(
            resource_with_comma_format.copy(), format_mapping=ogdch_mixin.format_mapping)
        self.assertEquals('CSV', resource_with_comma_format_cleaned['format'])
