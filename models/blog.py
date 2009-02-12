# -*- coding: utf-8 -*-
from urllib2 import unquote
from exceptions import Exception
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from datetime import datetime
from util.globals import url_for

class NonUniqueException(Exception):
    pass

class InvalidConstructorException(Exception):
    pass


class Author(db.Model):
    user     = db.UserProperty()
    fullname = db.StringProperty()

    def __str__(self):
        return '%s (%s)' % (self.fullname, self.user)

# monkeypatch googles User class (adding Author and Fullname)
def get_author_for_user(u):
    a = Author.all().filter('user =', u).get()
    if a is None:
        a = Author(user=u, fullname='Anonymous')
        a.put()
    return a

users.User.author = get_author_for_user
users.User.fullname = lambda self: get_author_for_user(self).fullname

class Post(db.Model):
    """Basic Blog post"""

    @classmethod
    def _s(cls):
        return cls.all().order('-sort_key')

    @classmethod
    def _rs(cls):
        return cls.all().order('sort_key')

    @classmethod
    def _pub(cls):
        return cls._s().filter('published = ', True)

    @classmethod
    def _rpub(cls):
        return cls._rs().filter('published = ', True)

    @classmethod
    def pub(cls):
        return cls._pub().filter('sort_key <=',
                                 u'%s' % datetime.now().strftime('%Y%m%d%H%M%S'))

    @classmethod
    def rpub(cls):
        return cls._rpub().filter('sort_key <=',
                                 u'%s' % datetime.now().strftime('%Y%m%d%H%M%S'))

    @classmethod
    def unpub(cls):
        return cls._s().filter('published =', False)

    @classmethod
    def runpub(cls):
        return cls._rs().filter('published =', False)

    @classmethod
    def upcoming(cls):
        return cls._pub().filter('sort_key >',
                                 u'%s' % datetime.now().strftime('%Y%m%d%H%M%S'))

    @classmethod
    def rupcoming(cls):
        return cls._rpub().filter('sort_key >',
                                 u'%s' % datetime.now().strftime('%Y%m%d%H%M%S'))

    author    = db.UserProperty()
    title     = db.StringProperty(required=True)
    slug      = db.StringProperty()
    # date is to sort datbased
    date      = db.DateProperty(auto_now_add=True)
    created   = db.DateTimeProperty(auto_now_add=True)
    modified  = db.DateTimeProperty(auto_now=True)
    city      = db.StringProperty(required=True)
    country   = db.StringProperty(required=True)
    topics    = db.StringListProperty()
    body      = db.TextProperty()
    html      = db.TextProperty()
    lookup    = db.StringProperty(required=True,default='')
    published = db.BooleanProperty(default=False)
    pub_date  = db.DateTimeProperty(required=True, default=datetime.now)
    sort_key  = db.StringProperty(required=True, default='--')
    version   = db.IntegerProperty(required=True, default=1)

    def next(self):
        return Post.pub().filter('sort_key <', self.sort_key).get()

    def prev(self):
        return Post.pub().filter('sort_key >', self.sort_key).get()

    def get_key_name(self):
        return self.key().id_or_name()

    def update_sort_key(self):
        self.sort_key = u'%s:%s' % (self.pub_date.strftime('%Y%m%d%H%M%S'), self.slug)

    def get_state(self):
        return {True: u'Published', False: u'Unpublished'}[self.published]

    def get_key(self):
        return self.get_key_name()

    def get_absolute_url(self, unquote_url=False):
        # ugly!
        key = self.get_key_name()
        if key.startswith('Published:'):
            key = key[10:]
        if not unquote_url:
            return url_for('articles/show', key=key)
        return unquote(url_for('articles/show', key=key))

    def is_cached(self):
        return memcache.get(self.get_absolute_url(unquote_url=True)) is not None

    def invalidate_cache(self):
        for i in range(2):
            if memcache.delete(self.get_absolute_url(unquote_url=True)) > 0:
                break
