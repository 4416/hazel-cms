# -*- coding: utf-8 -*-
from os import environ
from types import StringTypes
from functools import wraps

from logging import info
from datetime import datetime
from datetime import timedelta

from google.appengine.api import users
from google.appengine.api import memcache

from werkzeug import LocalManager
from werkzeug import Local

from hazel.debug import utils

from helper import render_template
from manage import local

Lfilter = {}
Lglobal = {}
Lconst  = {}
Jfilter = {}
Jglobal = {}
Jconst  = {}

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
            return render_template('no_access.html',request=request)
        return fn(request, *args, **kwargs)
    return _fn

# memcache decorator
def memcached(fn):
    @wraps(fn)
    def _fn(request, *args, **kwargs):
        key = request.path
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

def layout_filter(x):
    def reg(name, fn):
        Lfilter[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def jinja_filter(x):
    def reg(name, fn):
        Jfilter[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def layout_global(x):
    def reg(name, fn):
        Lglobal[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def jinja_global(x):
    def reg(name, fn):
        Jglobal[name] = fn
        return fn
    if isinstance(x, StringTypes):
        return lambda fn: reg(x, fn)
    return reg(x.__name__, x)

def layout_const(n,v):
    Lconst[n] = v
    return v

def jinja_const(n,v):
    Jconst[n] = v
    return v

def update_environment():
    local.layout_env.filters.update(Lfilter)
    local.layout_env.globals.update(Lconst)
    local.layout_env.globals.update(Lglobal)
    local.jinja_env.filters.update(Jfilter)
    local.jinja_env.globals.update(Jconst)
    local.jinja_env.globals.update(Jglobal)
