# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

def memcached(fn):
    def _fn(cls, key, **kwargs):
        obj = memcache.get(key)
        if obj:
            return obj
        obj = fn(cls, key, **kwargs)
        memcache.add(key, obj)
        return obj
    return _fn

class Settings(db.Expando):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    author = db.UserProperty()

    @classmethod
    @memcached
    def get_or_create(cls, key_name, **kwargs):
        obj = cls.get_or_insert(key_name, **kwargs)
        # making sure all args are really set.
        # app-engine has the habit of ignoring
        # keywords that are set to None
        dirty = False
        for k,v in kwargs.iteritems():
            if not hasattr(obj, k):
                setattr(obj,k,v)
                dirty = True
        if dirty:
            obj.put()
        return obj

    def invalidate(self):
        memcache.delete(self.key().id_or_name())

    def put(self):
        self.author = users.get_current_user()
        obj = super(Settings, self).put()
        self.invalidate()
        return obj
