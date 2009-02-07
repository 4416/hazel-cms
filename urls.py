# -*- coding: utf-8 -*-
from werkzeug.routing import Map, Rule

url_map = Map([
	Rule('/',                                 endpoint='articles/index'),
	Rule('/<path:key>',                       endpoint='articles/show'),
	Rule('/topic/<tag>/',                     endpoint='articles/topic'),
	Rule('/archive/',                         endpoint='articles/archive'),
	Rule('/admin/',                           endpoint='admin/index'),
#	Rule('/admin/<path:key>',                 endpoint='admin/show'),
#	Rule('/admin/create/',                    endpoint='admin/create'),
#	Rule('/admin/edit/<path:key>',            endpoint='admin/edit'),
#	Rule('/admin/delete/<path:key>',          endpoint='admin/delete'),
#	Rule('/admin/author/',                    endpoint='admin/author'),
#	Rule('/admin/migrate/<model>/',           endpoint='admin/migrate'),
	Rule('/feeds/<name>/',                    endpoint='feeds/show'),
	Rule('/fineprint',                        endpoint='tmpl/fineprint'),
	Rule('/page/<path:key>',                  endpoint='pages/show'),
	Rule('/file/<slug>.<type>',               endpoint='files/show'),
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
	Rule('/admin/cache/',                     endpoint='admin/cache/list'),
]) 

from views import blog, feeds, famfamfam, pages as pub_pages
from admin.views import pages, layouts, files, articles, cache
from models.pages import FOLDER
views = {
    'articles/index'    : blog.index,
    'articles/show'     : blog.show,
    'articles/topic'    : blog.topic,
    'articles/archive'  : lambda r: blog.topic(r,None),
#    'admin/index'   : admin.index,
#    'admin/create'  : admin.create,
#    'admin/edit'    : admin.edit,
#    'admin/delete'  : admin.delete,
#    'admin/memcache': admin.memcache,
#    'admin/memcache/flush': lambda r: admin.memcache(r,True),
#    'admin/migrate' : admin.migrate,
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
}
from util.decorators import require_admin
for key in views:
	if key.startswith('admin'):
		views[key] = require_admin(views[key])
