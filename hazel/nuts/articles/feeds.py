# -*- coding: utf-8 -*-
# global
from datetime import datetime
# appengine
# lib
from lib.atom import Feed
# local
from models import Post
from hazel.util.helper import render_jinja
from hazel.util.net import Response
from hazel import NutSettings as AppSettings
from hazel.nuts.articles import NutSettings
# relative
from urls import expose
from hazel.util.decorators import memcached

class MyFeed(Feed):
    appSettings = AppSettings()
    nutSettings = NutSettings()

    def setup(self, qs, n):
        now = datetime.now()
        self.feed_updated = datetime(1970,1,1)
        for post in qs.fetch(n):
            if post.modified > self.feed_updated:
                self.feed_updated = post.modified
        self.items = qs.fetch(n)
        return self

    base_url = 'http://%s' % appSettings.hosts[0]
    base_tag = 'tag:%s' % appSettings.hosts[0]

    feed_id = 'tag:%s' % '.'.join(appSettings.hosts[0].split('.')[:-1])
    feed_title = nutSettings.title
    feed_subtitle = nutSettings.subtitle
    feed_authors = [{'name': appSettings.admins[0][0], 'email': appSettings.admins[0][1]}]
    feed_links = [{'rel': 'alternate', 'href': '%s/' % base_url }]

    item_id = lambda s, i: '%s,%s:/%s' % (s.base_tag, i.date, i.lookup)
    item_title = lambda s, i: i.title
    item_updated = lambda s, i: i.modified
    item_published = lambda s, i: i.pub_date
    item_links = lambda s, i: [{'href': '%s/%s' % (s.base_url, i.lookup)}]
    def item_content(self, item):
        return {'type': 'html',
                'xml:base': '%s/' % self.base_url },\
                render_jinja('articles/feed_content.html', object=item)
    
@expose('/feeds/<name>/')
#@memcached
#FIXME: needs some extra logic / invalidator!
def feed(request, name):
    if name.startswith('tag-'):
        qs = Post.pub().filter('topics = ', name[4:])
    else:
        qs = Post.pub()
    feed = MyFeed(None,None).setup(qs,5).get_feed()
    response = Response(mimetype=feed.mime_type)
    feed.write(response.stream, 'utf-8')
    return response
