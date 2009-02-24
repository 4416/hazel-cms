# -*- coding: utf-8 -*-
from logging import info

from google.appengine.api import memcache

from werkzeug.routing import Map, Rule, EndpointPrefix, Submount
from hazel import NutSettings
from hazel import CACHE_KEY_URL

from views import famfamfam
from admin.views import configure


rules = lambda : [
    Rule('/admin/',                           endpoint='admin/index'),
    Rule('/famfamfam/<file>',                 endpoint='famfamfam/get'),
    Rule('/admin/configure/',           endpoint='admin/configuration'),
    Rule('/admin/pb/<kind>',            endpoint='admin/pb'),
#    Rule('/admin/migrate/',                   endpoint='admin/migrate'),
]

def build_urls():
    views = {
        'famfamfam/get' : famfamfam.get,
#        'admin/cache/list'    : cache.list,
#        'admin/migrate'       : pages.migrate,
        'admin/configuration'     : configure.nut,
        'admin/pb'             : configure.pb,
        'admin/index'          : configure.list
    }

    # secure the admin area
    from util.decorators import require_admin
    for key in views:
        if key.startswith('admin'):
            views[key] = require_admin(views[key])

    admin_tabs = []
    url_map = Map(rules())
    for nut in NutSettings().nuts:
        mod = __import__('hazel.nuts.%s.urls' % nut, fromlist=['hazel.nuts.%s' % nut])
        pub, pub_views, admin, admin_views, tabs = mod.build_rules()
        url_map.add(EndpointPrefix('nut:%s/' % nut, pub))
        url_map.add(EndpointPrefix('nut:%s/' % nut,
                                   [Submount('/admin/%s' % nut, admin)]))
        admin_tabs.extend([(rule.endpoint, name) for name, rule in tabs])
        views.update([(rule.endpoint, fn) for rule, fn in pub_views])
        # secure admin
        views.update([(rule.endpoint, require_admin(fn)) for rule, fn in admin_views])


    # tell the layout engine about the enabled modules
    from util.decorators import jinja_const
    jinja_const('admin_tabs', admin_tabs)

    return url_map, views
