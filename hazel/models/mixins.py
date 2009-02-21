# -*- coding: utf-8 -*-
from google.appengine.api import memcache

RETRY = 5

class CacheUtilMixin(object):
    def is_cached(self):
        return not memcache.get(self.cache_key()) == None

    def invalidate_cache(self):
        for i in range(RETRY):
            if memcache.delete(self.cache_key()) > 0:
                break
