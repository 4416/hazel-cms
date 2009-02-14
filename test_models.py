# -*- coding: utf-8 -*-
from models.pages import MethodMixin, Layout
from util.sortedmpnode import SortedMPNode
from google.appengine.ext import db
#class Test(SortedMPNode):
#       name     = db.StringProperty(default='root')
from logging import info

i = 0

info('yes! %d' % i)

class ABC(SortedMPNode, MethodMixin):
    type = db.IntegerProperty(default=1, required=True)
    name     = db.StringProperty(required=True, default='root')
    abs_path = db.StringProperty(default='')

    slug = db.StringProperty(default='')
    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()
    state = db.IntegerProperty(default=0)
    active = db.BooleanProperty(default=False)

    description = db.StringProperty()
    keywords = db.StringProperty()
    body = db.TextProperty()

    layout = db.ReferenceProperty(Layout)
    content_type = db.StringProperty(required=True, default='text/html')
