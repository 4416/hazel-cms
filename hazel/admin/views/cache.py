# -*- coding: utf-8 -*-
from google.appengine.api import memcache

from hazel.util.helper import render_template

def list(request):
    if request.args.get('flush',False):
        memcache.flush_all()
    return render_template('cache/list.html', memcache=memcache.get_stats())
