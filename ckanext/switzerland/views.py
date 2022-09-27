# encoding: utf-8
from ckan.views.feed import (_parse_url_params, _package_search,
                             _navigation_urls, _feed_url, _alternate_url,
                             _create_atom_id, SITE_TITLE)
from flask import Blueprint


def ogdch_output_feed(results, feed_title, feed_description, feed_link, feed_url,
                      navigation_urls, feed_guid):
    """Copied from ckan.views.feed so that we can make necessary overrides to fit
    our use case:
    1. Use our `updated` and `issued` fields for updated and published dates,
       not CKAN's `metadata_modified` and `metadata_published` fields
    2. Localize multilingual fields (`title` and `description`)
    """
    author_name = config.get(u'ckan.feeds.author_name', u'').strip() or \
                  config.get(u'ckan.site_id', u'').strip()

    # TODO: language
    feed_class = None
    for plugin in plugins.PluginImplementations(plugins.IFeed):
        if hasattr(plugin, u'get_feed_class'):
            feed_class = plugin.get_feed_class()

    if not feed_class:
        feed_class = _FixedAtom1Feed

    feed = feed_class(
        feed_title,
        feed_link,
        feed_description,
        language=u'en',
        author_name=author_name,
        feed_guid=feed_guid,
        feed_url=feed_url,
        previous_page=navigation_urls[u'previous'],
        next_page=navigation_urls[u'next'],
        first_page=navigation_urls[u'first'],
        last_page=navigation_urls[u'last'], )

    for pkg in results:
        additional_fields = {}

        for plugin in plugins.PluginImplementations(plugins.IFeed):
            if hasattr(plugin, u'get_item_additional_fields'):
                additional_fields = plugin.get_item_additional_fields(pkg)

        feed.add_item(
            title=pkg.get(u'title', u''),
            link=h.url_for(
                u'api.action',
                logic_function=u'package_read',
                id=pkg['id'],
                ver=3,
                _external=True),
            description=pkg.get(u'notes', u''),
            updated=h.date_str_to_datetime(pkg.get(u'metadata_modified')),
            published=h.date_str_to_datetime(pkg.get(u'metadata_created')),
            unique_id=_create_atom_id(u'/dataset/%s' % pkg['id']),
            author_name=pkg.get(u'author', u''),
            author_email=pkg.get(u'author_email', u''),
            categories=[t['name'] for t in pkg.get(u'tags', [])],
            enclosure=webhelpers.feedgenerator.Enclosure(
                h.url_for(
                    u'api.action',
                    logic_function=u'package_show',
                    id=pkg['name'],
                    ver=3,
                    _external=True),
                text_type(len(json.dumps(pkg))), u'application/json'),
            **additional_fields)

    resp = make_response(feed.writeString(u'utf-8'), 200)
    resp.headers['Content-Type'] = u'application/atom+xml'
    return resp


def general():
    """
    Copied from ckan.views.feed so that we can make necessary overrides to fit
    our use case:
    1. Sort package search results by our `updated` field, not CKAN's
       `metadata_modified` field
    """
    data_dict, params = _parse_url_params()
    data_dict['q'] = u'*:*'
    item_count, results = _package_search(data_dict)

    navigation_urls = _navigation_urls(
        params,
        item_count=item_count,
        limit=data_dict['rows'],
        controller=u'feeds',
        action=u'general')

    feed_url = _feed_url(params, controller=u'feeds', action=u'general')

    alternate_url = _alternate_url(params)

    guid = _create_atom_id(u'/feeds/dataset.atom')

    desc = u'Recently created or updated datasets on %s' % SITE_TITLE

    return ogdch_output_feed(
        results,
        feed_title=SITE_TITLE,
        feed_description=desc,
        feed_link=alternate_url,
        feed_guid=guid,
        feed_url=feed_url,
        navigation_urls=navigation_urls)


ogdch_feeds = Blueprint(u'ogdch_feeds', __name__, url_prefix=u'/feeds')
ogdch_feeds.add_url_rule(u'/dataset.atom', methods=[u'GET'], view_func=general)


def get_blueprints():
    return [ogdch_feeds]
