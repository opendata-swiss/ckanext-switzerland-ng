"""
helpers for preparing the resource format
belong in this file
"""
import yaml
import os
import urlparse

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)

LINKED_DATA_FORMATS = [
    'JSON-LD',
    'N3',
    'RDF N-Triples',
    'RDF Turtle',
    'RDF XML',
    'SPARQL',
]


class FormatMappingNotLoadedError(Exception):
    pass


def ogdch_get_format_mapping(mapping_type):
    """Read in a format mapping from a yaml file
    """
    mapping_path = os.path.join(
        __location__,
        '{}_mapping.yaml'.format(mapping_type)
    )
    try:
        with open(mapping_path, 'r') as mapping_file:
            mapping = yaml.safe_load(mapping_file)
            reverse_mapping = {}
            for key, format_list in mapping.iteritems():
                for format in format_list:
                    reverse_mapping[format] = key
    except (IOError, yaml.YAMLError) as exception:
        raise FormatMappingNotLoadedError(
            'Loading Format-Mapping from Path: (%s) '
            'failed with Exception: (%s)'
            % (mapping_path, exception)
        )

    return mapping, reverse_mapping


format_mapping, reverse_format_mapping = ogdch_get_format_mapping(
    mapping_type='format'
)
media_type_mapping, reverse_media_type_mapping = ogdch_get_format_mapping(
    mapping_type='media_type'
)


def prepare_resource_format(resource):
    """Determine resource format depending on media_type, format and
    download_url. Then convert media_type to its IANA value.
    """
    resource['format'] = get_resource_format(
        media_type=resource.get('media_type'),
        format=resource.get('format'),
        download_url=resource.get('download_url')
    )
    resource['media_type'] = get_iana_media_type(resource.get('media_type'))
    return resource


def get_resource_format(media_type, format, download_url):
    """the format of the resource is derived in the following way:
    the first matching case is taken
    - case 1 media_type is set and matches as format
             from the format list: this format will be taken
    - case 2 format is set: check whether the format is already mapped
             or whether it can be mapped
    - case 3 download url is set: check if the format can be derived
             from the file extention, otherwise if the media type is
             set and valid take the media type as format, otherwise
             set it as blank
    - case 4 no download url: set the format to SERVICE
    """
    if media_type:
        cleaned_media_type = _get_cleaned_format_or_media_type(media_type)
        format_from_media_type = _map_to_valid_format(cleaned_media_type)
        if format_from_media_type:
            return format_from_media_type

    if format:
        format_from_format = _map_to_valid_format(format, try_to_clean=True)
        if format_from_format:
            return format_from_format

    if download_url:
        format_from_file_extension = _get_format_from_path(download_url)
        if format_from_file_extension:
            return format_from_file_extension
        elif media_type:
            return cleaned_media_type
        return ""

    return 'SERVICE'


def get_iana_media_type(media_type):
    """Get a value for media_type that belongs to the IANA Media Types
    vocabulary, if there is one. Otherwise, return the media_type as it is.
    """
    if not media_type:
        return ""

    iana_media_type = _map_to_valid_media_type(
        _get_cleaned_format_or_media_type(media_type)
    )
    if iana_media_type:
        return iana_media_type

    return media_type


def prepare_formats_for_index(resources, linked_data_only=False):
    """Generate a deduplicated list with formats of all resources, or all
    Linked Data formats that are present.
    """
    formats = set()
    for r in resources:
        resource = prepare_resource_format(
            resource=r
        )
        if linked_data_only \
                and resource.get('format') not in LINKED_DATA_FORMATS:
            continue
        if resource['format']:
            formats.add(resource['format'])
        else:
            formats.add('N/A')

    return list(formats)


def _map_to_valid_format(format, try_to_clean=False):
    """Check whether the format is in the format mapping, either as a key or
    as a value, or if it can be derived after cleaning the input format string
    """
    if format in format_mapping.keys():
        return format

    if format in reverse_format_mapping.keys():
        return reverse_format_mapping[format]
    if try_to_clean:
        cleaned_format = _get_cleaned_format_or_media_type(format)
        if cleaned_format in reverse_format_mapping.keys():
            return reverse_format_mapping[cleaned_format]
    return ""


def _map_to_valid_media_type(media_type, try_to_clean=False):
    """Check whether the media_type is in the mapping, either as a key or as a
    value, or if it can be derived after cleaning the input media_type string
    """
    if media_type in media_type_mapping.keys():
        return media_type

    if media_type in reverse_media_type_mapping.keys():
        return reverse_media_type_mapping[media_type]
    if try_to_clean:
        cleaned_media_type = _get_cleaned_format_or_media_type(media_type)
        if cleaned_media_type in reverse_media_type_mapping.keys():
            return reverse_media_type_mapping[cleaned_media_type]
    return ""


def _get_cleaned_format_or_media_type(format):
    """clean the format"""
    if format:
        cleaned_format = format.split('/')[-1].lower()
        if cleaned_format:
            return cleaned_format
    return ""


def _get_format_from_path(download_url):
    """check whether the format can be derived from the file
    extension"""
    path = urlparse.urlparse(download_url).path
    ext = os.path.splitext(path)[1]
    if ext:
        resource_format = ext.replace('.', '').lower()
        return _map_to_valid_format(resource_format)
    return ""
