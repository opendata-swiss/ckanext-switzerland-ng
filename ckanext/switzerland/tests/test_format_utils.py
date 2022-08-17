"""Tests for helpers.format_utils.py."""
import ckanext.switzerland.helpers.format_utils as ogdch_format_utils
from nose.tools import *  # noqa
import os

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


prepare_resource_data = [
    ({
        'download_url': None,
        'media_type': None,
        'format': None
    }, 'SERVICE'),
    ({
        'download_url': 'http://download.url',
        'media_type': None,
        'format': 'dogvideo'
    }, ''),
    ({
        'download_url': 'http://download.url',
        'media_type': None,
        'format': None
    }, ''),
    ({
        'download_url': None,
        'media_type': None,
        'format': 'catgif'
    }, 'SERVICE'),
    ({
        'download_url': None,
        'media_type': None,
        'format': 'xml'
    }, 'XML'),
    ({
         'download_url': 'http://download.url',
         'media_type': 'cat/gif',
         'format': 'gif'
     }, 'gif'),
    ({
         'download_url': None,
         'media_type': 'html',
         'format': 'xml'
     }, 'HTML'),
    ({
         'download_url': None,
         'media_type': 'text/html',
         'format': 'xml'
     }, 'HTML'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'application/vnd.oas...'
     }, 'ODS'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
     }, 'XLS'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'pc-axis file'
     }, 'PC-AXIS'),
    ({
         'download_url': 'http://download.url/Download.aspx?file=pc-axis-file-001',
         'media_type': 'pc-axis file',
         'format': 'CSV'
     }, 'PC-AXIS'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'Application/Sparql-...'
     }, 'RDF'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'ESRI Shapefile'
     }, 'SHP'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'text (.txt)'
     }, 'TXT'),
    ({
         'download_url': 'http://download.url',
         'media_type': None,
         'format': 'comma ...'
     }, 'CSV'),
    ({
         'download_url': None,
         'media_type': None,
         'format': 'SHP'
     }, 'SHP'),
    ({
         'download_url': 'http://download.url',
         'media_type': 'text/xml',
         'format': 'html'
     }, 'XML'),
    ({
         'download_url': 'http://download.url/cat.gif?param=1',
         'media_type': '',
         'format': ''
     }, ''),
    ({
         'download_url': 'http://download.url/cat.gif?param=1',
         'media_type': 'text/xml',
         'format': 'xml'
     }, 'XML'),
    ({
         'download_url': 'http://download.url/file.zip?param=1',
         'media_type': '',
         'format': ''
     }, 'ZIP'),
    ({
         'download_url': 'http://download.url/file.zip?param=1',
         'media_type': 'text/xml',
         'format': 'xml'
     }, 'XML'),
    ({
         'download_url': None,
         'media_type': None,
         'format': 'esri shapefile'
     }, 'SHP'),
]


def _check_prepare_resource_format(resource_data, expected_format):
    cleaned_resource = ogdch_format_utils.prepare_resource_format(resource_data.copy())
    assert expected_format == cleaned_resource['format']


def test_prepare_resource_format():
    for r in prepare_resource_data:
        yield _check_prepare_resource_format, r[0], r[1]
