# -*- coding: utf-8 -*-

from werkzeug.routing import Rule
from werkzeug.routing import Submount
from werkzeug.routing import Subdomain

from . import NutSettings

public = []
admin = []

def expose(rule, **kw):
    def decorate(fn):
        kw['endpoint'] = fn.__name__
        public.append((rule, fn, kw))
        return fn
    return decorate

def expose_admin(rule, tab=None, **kw):
    def decorate(fn):
        kw['endpoint'] = fn.__name__
        admin.append((rule, fn, tab, kw))
        return fn
    return decorate

def _build_rules():
    pub_views = []
    pub_rules = []
    admin_views = []
    admin_rules = []
    admin_tabs = []
    for rule, fn, kw in public:
        r = Rule(rule, **kw)
        pub_rules.append(r)
        pub_views.append((r,fn))
    for rule, fn, tab, kw in admin:
        r = Rule(rule, **kw)
        admin_rules.append(r)
        admin_views.append((r,fn))
        if tab:
            admin_tabs.append((tab, r))
    return pub_rules, pub_views, admin_rules, admin_views, admin_tabs

def build_rules():
    return _build_rules()
