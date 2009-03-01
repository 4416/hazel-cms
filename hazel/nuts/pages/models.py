# -*- coding: utf-8 -*-
import re

from google.appengine.ext import db

from hazel.util.globals import url_for

from hazel.models import AbsPathSMPNode
from hazel.models import CacheUtilMixin

from hazel.nuts.layouts.models import Layout

HIDDEN    = 0
DRAFT     = 1
PUBLISHED = 2

FOLDER = 0
PAGE   = 1
FILE   = 2

class Node(AbsPathSMPNode, CacheUtilMixin):

    _endpoint = 'nut:pages/show'

    type = db.IntegerProperty(default=FOLDER, required=True) 

    name = db.StringProperty(required=True, default='root')

#    abs_path = db.StringProperty(default='')

#    slug = db.StringProperty(default='')
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

    def get_state(self):
        if self.active:
            return {HIDDEN   : u'Hidden',
                    DRAFT    : u'Draft',
                    PUBLISHED: u'Published' }[self.state]
        else:
            return u'Disabled'

    def get_ancestors(self):
        return db.get(self.ancestors)

    def cache_key(self):
        return url_for(self._endpoint, _external=True, key=self.abs_path)

class Block(db.Model):
    node = db.ReferenceProperty(Node, collection_name='blocks')
    name = db.StringProperty(required=True)
    body = db.TextProperty()
