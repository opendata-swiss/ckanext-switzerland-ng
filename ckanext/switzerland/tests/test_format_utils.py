"""Tests for helpers.format_utils.py."""

import os

import pytest

import ckanext.switzerland.helpers.format_utils as ogdch_format_utils

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


prepare_resource_data = [
    ({"download_url": None, "media_type": None, "format": None}, "SERVICE"),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "dogvideo",
        },
        "",
    ),
    ({"download_url": "http://download.url", "media_type": None, "format": None}, ""),
    ({"download_url": None, "media_type": None, "format": "catgif"}, "SERVICE"),
    ({"download_url": None, "media_type": None, "format": "xml"}, "XML"),
    (
        {
            "download_url": "http://download.url",
            "media_type": "cat/gif",
            "format": "gif",
        },
        "gif",
    ),
    ({"download_url": None, "media_type": "html", "format": "xml"}, "HTML"),
    ({"download_url": None, "media_type": "text/html", "format": "xml"}, "HTML"),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "application/vnd.oas...",
        },
        "ODS",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
        "XLS",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "pc-axis file",
        },
        "PC-AXIS",
    ),
    (
        {
            "download_url": "http://download.url/Download.aspx?file=pc-axis-file-001",
            "media_type": "pc-axis file",
            "format": "CSV",
        },
        "PC-AXIS",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "Application/Sparql-...",
        },
        "SPARQL",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": "application/sparql-query",
            "format": None,
        },
        "SPARQL",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "rq"},
        "SPARQL",
    ),
    (
        {
            "download_url": "http://download.url/foo.sparqlq",
            "media_type": None,
            "format": None,
        },
        "SPARQL",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": "application/ld+json",
            "format": None,
        },
        "JSON-LD",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "jsonld"},
        "JSON-LD",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "json_ld",
        },
        "JSON-LD",
    ),
    (
        {
            "download_url": "http://download.url/foo",
            "media_type": "text/n3",
            "format": None,
        },
        "N3",
    ),
    ({"download_url": "http://download.url", "media_type": None, "format": "n3"}, "N3"),
    (
        {
            "download_url": "http://download.url/foo.n3",
            "media_type": None,
            "format": None,
        },
        "N3",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": "application/rdf+xml",
            "format": None,
        },
        "RDF XML",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "rdf"},
        "RDF XML",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "rdf_xml",
        },
        "RDF XML",
    ),
    (
        {
            "download_url": "http://download.url/foo.rdf",
            "media_type": None,
            "format": None,
        },
        "RDF XML",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": "application/n-triples",
            "format": None,
        },
        "RDF N-Triples",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "nt"},
        "RDF N-Triples",
    ),
    (
        {
            "download_url": "http://download.url/foo.nt",
            "media_type": None,
            "format": None,
        },
        "RDF N-Triples",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": "text/turtle",
            "format": None,
        },
        "RDF Turtle",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "ttl"},
        "RDF Turtle",
    ),
    (
        {
            "download_url": "http://download.url/foo.ttl",
            "media_type": None,
            "format": None,
        },
        "RDF Turtle",
    ),
    (
        {"download_url": "http://download.url", "media_type": "turtle", "format": None},
        "RDF Turtle",
    ),
    (
        {"download_url": "http://download.url", "media_type": None, "format": "ttl"},
        "RDF Turtle",
    ),
    (
        {
            "download_url": "http://download.url/foo.ttl",
            "media_type": None,
            "format": None,
        },
        "RDF Turtle",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "ESRI Shapefile",
        },
        "SHP",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "text (.txt)",
        },
        "TXT",
    ),
    (
        {
            "download_url": "http://download.url",
            "media_type": None,
            "format": "comma ...",
        },
        "CSV",
    ),
    ({"download_url": None, "media_type": None, "format": "SHP"}, "SHP"),
    (
        {
            "download_url": "http://download.url",
            "media_type": "text/xml",
            "format": "html",
        },
        "XML",
    ),
    (
        {
            "download_url": "http://download.url/cat.gif?param=1",
            "media_type": "",
            "format": "",
        },
        "",
    ),
    (
        {
            "download_url": "http://download.url/cat.gif?param=1",
            "media_type": "text/xml",
            "format": "xml",
        },
        "XML",
    ),
    (
        {
            "download_url": "http://download.url/file.zip?param=1",
            "media_type": "",
            "format": "",
        },
        "ZIP",
    ),
    (
        {
            "download_url": "http://download.url/file.zip?param=1",
            "media_type": "text/xml",
            "format": "xml",
        },
        "XML",
    ),
    ({"download_url": None, "media_type": None, "format": "esri shapefile"}, "SHP"),
    (
        {
            "download_url": "http://download.url/file.asc",
            "media_type": None,
            "format": "grid_ascii",
        },
        "ESRI ASCII Grid",
    ),
    (
        {
            "download_url": "http://download.url/file.asc",
            "media_type": "text/plain",
            "format": "grid_ascii",
        },
        "TXT",
    ),
    (
        {
            "download_url": "http://download.url/file",
            "media_type": None,
            "format": "world",
        },
        "WORLDFILE",
    ),
    (
        {
            "download_url": "http://download.url/file",
            "media_type": None,
            "format": "wmts_srvc",
        },
        "WMTS",
    ),
]


@pytest.mark.parametrize("resource_data, expected_format", prepare_resource_data)
def test_prepare_resource_format(resource_data, expected_format):
    cleaned_resource = ogdch_format_utils.prepare_resource_format(resource_data.copy())
    assert expected_format == cleaned_resource["format"]


prepare_formats_data = [
    (
        [{"media_type": "rdf+xml"}, {"media_type": "png"}],
        True,
        ["RDF XML"],
    ),
    (
        [{"media_type": "rdf+xml"}, {"media_type": "png"}],
        False,
        ["RDF XML", "PNG"],
    ),
    (
        [
            {"media_type": "rdf+xml"},
            {"media_type": "rdf+xml"},
            {"media_type": "png"},
        ],
        False,
        ["RDF XML", "PNG"],
    ),
    (
        [
            {"media_type": "ld+json"},
            {"media_type": "n3"},
            {"media_type": "n-triples"},
            {"media_type": "turtle"},
            {"media_type": "rdf+xml"},
            {"media_type": "sparql-query"},
        ],
        True,
        [
            "N3",
            "SPARQL",
            "JSON-LD",
            "RDF XML",
            "RDF N-Triples",
            "RDF Turtle",
        ],
    ),
]


@pytest.mark.parametrize(
    "resources, linked_data_only, expected_formats", prepare_formats_data
)
def test_prepare_formats_for_index(resources, linked_data_only, expected_formats):
    prepared_formats = ogdch_format_utils.prepare_formats_for_index(
        resources, linked_data_only
    )
    assert sorted(prepared_formats) == sorted(expected_formats)
