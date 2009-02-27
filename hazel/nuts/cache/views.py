# -*- coding: utf-8 -*-
from google.appengine.api import memcache

from hazel.util.helper import render_template

from urls import expose_admin

@expose_admin('/cache/', tab='Cache')
def list(request):
    if request.args.get('flush',False):
        memcache.flush_all()
    return render_template('app:cache/list.html', memcache=memcache.get_stats())
