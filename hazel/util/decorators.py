# -*- coding: utf-8 -*-
from os import environ
from types import StringTypes
from functools import wraps

from logging import info
from datetime import datetime
from datetime import timedelta

from google.appengine.api import users
from google.appengine.api import memcache

from hazel.debug import utils
from hazel.util import local

from helper import render_template
from hazel import jinja_env
from hazel import layout_env

################################################################################
# DebuggedApplication Decorator
################################################################################
def debugged(app):
    if 'SERVER_SOFTWARE' in environ and environ['SERVER_SOFTWARE'].startswith('Dev'):
        # use our debug.utils with Jinja2 templates
        import sys
        sys.modules['werkzeug.debug.utils'] = utils

        # don't use inspect.getsourcefile because the imp module is empty
        import inspect
        inspect.getsourcefile = inspect.getfile

        # wrap the application
        from werkzeug import DebuggedApplication
        app = DebuggedApplication(app, evalex=True)
    return app

################################################################################
# decorator
################################################################################
def require_admin(fn):
    def _fn(request, *args, **kwargs):
        if not users.is_current_user_admin():
            return render_template('no_access.html')
        return fn(request, *args, **kwargs)
    return _fn

# memcache decorator
def memcached(fn):
    @wraps(fn)
    def _fn(request, *args, **kwargs):
        key = local.adapter.build(local.endpoint, local.args, force_external=True)
        resp = memcache.get(key)
        if resp is not None:
            return resp
        resp = fn(request, *args, **kwargs)
        if getattr(resp,'prevent_cache', False):
            return resp
        resp.expires = datetime.now() + timedelta(7)
        memcache.add(key, resp)
        return resp
    return _fn

def memcached_for(time):
    """ creates a memcached decorator for a given period.
        valid values for t ar either absolute integers as seconds.
        or strings like '4s', '3m', '1h', '10d', '4w'

        This method may raise a ValueError or a KeyError if the
        format is not accepted!
    """
    def deco(fn,t):
        @wraps(fn)
        def _fn(request, *args, **kwargs):
            key = local.adapter.build(local.endpoint, local.args, force_external=True)
            resp = memcache.get(key)
            if resp is not None:
                return resp
            resp = fn(request, *args, **kwargs)
            if getattr(resp,'prevent_cache', False):
                return resp
            resp.expires = datetime.now() + timedelta(7)
            memcache.add(key, resp)
            return resp
        return resp
    if isinstance(time, int):
        return lambda fn: deco(fn,time)
    time_map = { 'w': 7 * 24 * 60 * 60,
                 'd':     24 * 60 * 60,
                 'h':          60 * 60,
                 'm':               60,
                 's':                1 }
    num, key = int(time[:-1]), time[-1]
    return lambda fn: defo(fn, num * time_map[key])
    

def layout_filter(x):
    def reg(name, fn):
        layout_env.filters[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def jinja_filter(x):
    def reg(name, fn):
        jinja_env.filters[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def layout_global(x):
    def reg(name, fn):
        layout_env.globals[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def jinja_global(x):
    def reg(name, fn):
        jinja_env.globals[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def layout_const(n,v):
    layout_env.globals[n] = v
    return v

def jinja_const(n,v):
    jinja_env.globals[n] = v
    return v
