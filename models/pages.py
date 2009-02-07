# -*- coding: utf-8 -*-
from util.models import SortedMPNode
from google.appengine.ext import db
from google.appengine.api import memcache
import utils
from logging import info

HIDDEN    = 0
DRAFT     = 1
PUBLISHED = 2

FOLDER = 0
PAGE   = 1
FILE   = 2

class MethodMixin(object):
    def get_state(self):
        if self.active:
            return {HIDDEN   : u'Hidden',
                    DRAFT    : u'Draft',
                    PUBLISHED: u'Published' }[self.state]
        else:
            return u'Disabled'

    def get_absolute_url(self, base=''):
        # FIXME: once the abs_path logic is fully implemented,
        #        this should be fixed accordingly
        if self.abs_path != '':
            return utils.url_for('pages/show', key=self.abs_path)
        return utils.url_for('pages/show', key=self.slug)

    def is_cached(self):
        return not memcache.get(self.get_absolute_url()) == None

    def invalidate_cache(self):
        for i in range(2):
            if memcache.delete(self.get_absolute_url()) > 0:
                break


class Layout(db.Model):
    name = db.StringProperty(required=True)
    body = db.TextProperty()

    author = db.UserProperty()
    updated = db.DateTimeProperty()

    active = db.BooleanProperty(default=True)

    def __unicode__(self):
        return u'Layout:%s' % self.key()

    def get_state(self):
        if self.active:
            return u'Enabled'
        else:
            return u'Disabled'

    def get_key(self):
        return u'%s' % self.key()


class Node(SortedMPNode, MethodMixin):
    type = db.IntegerProperty(default=FOLDER, required=True)

    name = db.StringProperty(required=True, default='root')

    abs_path = db.StringProperty(default='')

    slug = db.StringProperty(default='')
    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()
    state = db.IntegerProperty(default=HIDDEN)
    active = db.BooleanProperty(default=False)

    description = db.StringProperty()
    keywords = db.StringProperty()
    body = db.TextProperty()

    layout = db.ReferenceProperty(Layout)
    content_type = db.StringProperty(required=True, default='text/html')

class Block(db.Model):
    node = db.ReferenceProperty(Node, collection_name='blocks')
    name = db.StringProperty(required=True)
    body = db.TextProperty()

class File(SortedMPNode, MethodMixin):
    type = db.IntegerProperty(default=FOLDER, required=True)
    name = db.StringProperty(required=True, default='root')

    abs_path = db.StringProperty(default='')

    slug = db.StringProperty(default='')
    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()

    state = db.IntegerProperty(default=HIDDEN)
    active = db.BooleanProperty(default=False)

    content_type = db.StringProperty()
    data = db.BlobProperty()
    size = db.IntegerProperty(default=0)
