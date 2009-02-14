# -*- coding: utf-8 -*-
from logging import info

from google.appengine.api import memcache

from werkzeug.routing import Map, Rule, EndpointPrefix
from hazel import NutSettings
from hazel import CACHE_KEY_URL

from views import blog, feeds, famfamfam, pages as pub_pages
from admin.views import pages, layouts, files, articles, cache, configure
from models.pages import FOLDER


rules = lambda : [
    Rule('/admin/',                           endpoint='admin/index'),
    Rule('/feeds/<name>/',                    endpoint='feeds/show'),
    Rule('/fineprint',                        endpoint='tmpl/fineprint'),
    Rule('/file/<path:key>.<type>',           endpoint='files/show'),
    Rule('/famfamfam/<file>',                 endpoint='famfamfam/get'),
    Rule('/admin/pages/',                     endpoint='admin/pages/list'),
    Rule('/admin/pages/add/',                 endpoint='admin/pages/add'),
    Rule('/admin/pages/add/<key>/',           endpoint='admin/pages/add_to'),
    Rule('/admin/pages/add_folder/',          endpoint='admin/pages/add_folder'),
    Rule('/admin/pages/edit/<key>/',          endpoint='admin/pages/edit'),
    Rule('/admin/pages/delete/<key>/',        endpoint='admin/pages/delete'),
    Rule('/admin/pages/move/<A>/<mode>/<B>/', endpoint='admin/pages/move'),
    Rule('/admin/layouts/',                   endpoint='admin/layouts/list'),
    Rule('/admin/layouts/add/',               endpoint='admin/layouts/add'),
    Rule('/admin/layouts/edit/<key>/',        endpoint='admin/layouts/edit'),
    Rule('/admin/layouts/delete/<key>/',      endpoint='admin/layouts/delete'),
    Rule('/admin/files/',                     endpoint='admin/files/list'),
    Rule('/admin/files/add/',                 endpoint='admin/files/add'),
    Rule('/admin/files/add/<key>/',           endpoint='admin/files/add_to'),
    Rule('/admin/files/add_folder/',          endpoint='admin/files/add_folder'),
    Rule('/admin/files/edit/<key>/',          endpoint='admin/files/edit'),
    Rule('/admin/files/delete/<key>/',        endpoint='admin/files/delete'),
    Rule('/admin/files/move/<A>/<mode>/<B>/', endpoint='admin/files/move'),
    Rule('/admin/articles/',                  endpoint='admin/articles/list'),
    Rule('/admin/articles/add/',              endpoint='admin/articles/add'),
    Rule('/admin/articles/edit/<path:key>',   endpoint='admin/articles/edit'),
    Rule('/admin/articles/delete/<path:key>', endpoint='admin/articles/delete'),
    Rule('/admin/configure/',           endpoint='admin/configuration'),
    Rule('/admin/cache/',                     endpoint='admin/cache/list'),
    Rule('/admin/migrate/',                   endpoint='admin/migrate'),
]

def build_urls():
    views = {
        'articles/index'    : blog.index,
        'articles/show'     : blog.show,
        'articles/topic'    : blog.topic,
        'articles/archive'  : lambda r: blog.topic(r,None),
        'feeds/show'    : feeds.show,
        'tmpl/fineprint': lambda r: blog.direct(r,'fineprint.html'),
        'pages/show'    : pub_pages.show,
        'files/show'    : files.show,
        'famfamfam/get' : famfamfam.get,
        'admin/pages/list'    : pages.list_pages,
        'admin/pages/move'    : pages.move,
        'admin/pages/add'     : pages.add,
        'admin/pages/add_to'  : lambda r, key: pages.add(r, to=key),
        'admin/pages/add_folder': pages.add_folder,
        'admin/pages/edit'    : pages.edit,
        'admin/pages/delete'  : pages.delete,
        'admin/layouts/list'  : layouts.list,
        'admin/layouts/add'   : layouts.add,
        'admin/layouts/edit'  : layouts.edit,
        'admin/layouts/delete': layouts.delete,
        'admin/files/list'    : files.list,
        'admin/files/add'     : files.add,
        'admin/files/add_to'  : lambda r, key: files.add(r,to=key),
        'admin/files/add_folder' : lambda r: files.add(r,type=FOLDER),
        'admin/files/edit'    : files.edit,
        'admin/files/delete'  : files.delete,
        'admin/files/move'    : files.move,
        'admin/articles/list' : articles.list,
        'admin/articles/add'  : articles.add,
        'admin/articles/edit' : articles.edit,
        'admin/articles/delete' : articles.delete,
        'admin/cache/list'    : cache.list,
        'admin/migrate'       : pages.migrate,
        'admin/configuration'     : configure.nut
    }
    from util.decorators import require_admin
    for key in views:
        if key.startswith('admin'):
            views[key] = require_admin(views[key])
    url_map = memcache.get(CACHE_KEY_URL)
    if url_map:
        return url_map, views
    _rules = []
    for nut in NutSettings().nuts:
        exec 'from hazel.nuts.%s.urls import build_rules' % nut in locals()
        loc = locals()
        _rules.append(EndpointPrefix('%s/' % nut, loc['build_rules']()))
        del loc['build_rules']
    url_map = Map(rules() + _rules)
    # secure the admin area
    memcache.add(CACHE_KEY_URL, url_map)
    return url_map, views
