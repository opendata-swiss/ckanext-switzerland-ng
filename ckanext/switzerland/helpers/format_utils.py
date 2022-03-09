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


class FormatMappingNotLoadedError(Exception):
    pass


def ogdch_get_format_mapping():
    """reads in the format mapping from a yaml file"""
    try:
        mapping_path = os.path.join(__location__, 'mapping.yaml')
        with open(mapping_path, 'r') as format_mapping_file:
            format_mapping = yaml.safe_load(format_mapping_file)
            reverse_format_mapping = {}
            for key, format_list in format_mapping.iteritems():
                for format in format_list:
                    reverse_format_mapping[format] = key
    except (IOError, yaml.YAMLError) as exception:
        raise FormatMappingNotLoadedError(
            'Loading Format-Mapping from Path: (%s) '
            'failed with Exception: (%s)'
            % (mapping_path, exception)
        )

    return format_mapping, reverse_format_mapping


format_mapping, reverse_format_mapping = ogdch_get_format_mapping()


def prepare_resource_format(resource):
    """the format of the resource is derived in the following way:
    the first matching case is taken
    - case 1 media_type is set: it is derived from the media type
    - case 2 format is set: check whether the format is already mapped
             or whether it can be mapped
    - case 3 download url is set: check if the format can be derived
             from the file extention, otherwise set it as blank
    - case 4 no download url: set the format to SERVICE
    """
    media_type = resource.get('media_type')

    if media_type:
        resource_format = _get_format_from_media_type(media_type)
        if resource_format:
            resource['format'] = resource_format
            return resource

    format = resource.get('format')
    resource_format = _map_to_valid_format(format)
    if resource_format:
        resource['format'] = resource_format
        return resource

    if resource.get('download_url'):
        resource_format = _get_format_from_path(resource)
        if resource_format:
            resource['format'] = resource_format
        else:
            resource['format'] = 'SERVICE'
        return resource

    resource['format'] = ''
    return resource


def prepare_formats_for_index(resources):
    """generates a set with formats of all resources"""
    formats = set()
    for r in resources:
        resource = prepare_resource_format(
            resource=r
        )
        if resource['format']:
            formats.add(resource['format'])
        else:
            formats.add('N/A')

    return list(formats)


# all formats that need to be mapped have to be entered in the mapping.yaml
def _map_to_valid_format(format):
    """check whether the format if in the mapping:
    either as a key or as a value or if it can be derived
    after cleaning the input format string"""
    if format in format_mapping.keys():
        return format

    if format in reverse_format_mapping.keys():
        return reverse_format_mapping[format]

    format = _get_cleaned_format(format)
    if format in reverse_format_mapping.keys():
        return reverse_format_mapping[format]

    return None


def _get_format_from_media_type(media_type):
    """check whether a format can be derived from the
    media type"""
    cleaned_media_type = media_type.split('/')[-1].lower()
    return _map_to_valid_format(cleaned_media_type)


def _get_cleaned_format(format):
    """clean the format"""
    cleaned_format = format.split('/')[-1].lower()
    return cleaned_format


def _get_format_from_path(resource):
    """check whether the format can be derived from the file
    extension"""
    path = urlparse.urlparse(resource['download_url']).path
    ext = os.path.splitext(path)[1]
    if ext:
        resource_format = ext.replace('.', '').lower()
        return _map_to_valid_format(resource_format)
    return False
