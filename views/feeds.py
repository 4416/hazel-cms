# -*- coding: utf-8 -*-
from utils import render_jinja, Response
from atom import Feed
from models.blog import Post

from usersettings import ADMINS, ALLOWED_HOSTS, BLOG_TITLE, BLOG_SUBTITLE
fid = FEED_INFO_DICT = {'author': { 'name':  ADMINS[0][0],
                                    'email': ADMINS[0][1] },
                        'base_url': 'http://%s' % ALLOWED_HOSTS[0],
                        'base_tag': 'tag:%s' % ALLOWED_HOSTS[0],
                        'id': 'tag:%s' % '.'.join(ALLOWED_HOSTS[0].split('.')[:-1]),
                        'title': BLOG_TITLE,
                        'subtitle': BLOG_SUBTITLE }

class MyFeed(Feed):

    def setup(self, qs, n):
        from datetime import datetime
        now = datetime.now()
        self.feed_updated = datetime(1970,1,1)
        for post in qs.fetch(n):
            if post.modified > self.feed_updated:
                self.feed_updated = post.modified
        self.items = qs.fetch(n)
        return self

    feed_id, feed_title, feed_subtitle = fid['id'], fid['title'], fid['subtitle']
    feed_authors = [fid['author']]
    feed_links = [{'rel': 'alternate', 'href': '%s/' % fid['base_url']}]

    item_id = lambda s, i: fid['base_tag'] + ',' + str(i.date) + ':/' + i.lookup
    item_title = lambda s, i: i.title
    item_updated = lambda s, i: i.modified
    item_published = lambda s, i: i.pub_date
    item_links = lambda s, i: [{'href': '%s%s' % (fid['base_url'], '/' + i.lookup)}]
    def item_content(self, item):
        return {'type': 'html',
                'xml:base': '%s/' % fid['base_url']},\
                render_jinja('feed_content.html', object=item)

def show(request, name):
    if name.startswith('tag-'):
        qs = Post.pub().filter('topics = ', name[4:])
    else:
        qs = Post.pub()
    feed = MyFeed(None,None).setup(qs,5).get_feed()
    response = Response(mimetype=feed.mime_type)
    feed.write(response.stream, 'utf-8')
    return response
