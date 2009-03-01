# -*- coding: utf-8 -*-
from google.appengine.ext import db

from hazel.models import AbsPathSMPNode
from hazel.models import CacheUtilMixin

from hazel.util.constants import content_type_to_file_ext

from hazel.util.globals import url_for

HIDDEN    = 0
DRAFT     = 1
PUBLISHED = 2

FOLDER = 0
PAGE   = 1
FILE   = 2

class File(AbsPathSMPNode, CacheUtilMixin):

    _endpoint = 'nut:files/show'

    type = db.IntegerProperty(default=FOLDER, required=True)
    name = db.StringProperty(required=True, default='root')

    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()

    state = db.IntegerProperty(default=HIDDEN)
    active = db.BooleanProperty(default=False)

    content_type = db.StringProperty()
    data = db.BlobProperty()
    size = db.IntegerProperty(default=0)

    def get_state(self):
        if self.active:
            return {HIDDEN   : u'Hidden',
                    DRAFT    : u'Draft',
                    PUBLISHED: u'Published' }[self.state]
        else:
            return u'Disabled'


    def get_absolute_url(self):
        if self.abs_path is not None:
            return url_for(self._endpoint, key=self.abs_path,
                           type=content_type_to_file_ext[self.content_type])
        return ''

    def cache_key(self):
        return url_for(self._endpoint, _external=True, key=self.abs_path,
                       type=content_type_to_file_ext[self.content_type])
