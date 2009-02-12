# -*- coding: utf-8 -*-

from manage import local

from decorators import jinja_global
from decorators import layout_global

@jinja_global
def url_for(endpoint, _external=False, **values):
    url = local.adapter.build(endpoint, values, force_external=_external)
    if url.startswith(u'/'):
        return url
    return u'/' + url

@layout_global
def menu(root='root'):
    base = Node.all().filter('name = ', root).get()
    qs = Node.all().filter('active = ', True).filter('state = ', PUBLISHED)
    l = len(base.path)
    nodes = dict([(n.get_key(), n) for n in qs if n.path.startswith(base.path)])
    node = simple_rec(base, nodes)
    info(node)
    return node

@layout_global('file')
def file_path(slug):
    f = File.all().filter('slug = ', slug).get()
    if f is None:
        return u''
    return f.get_absolute_url()

@layout_global('file')
def page_path(slug):
    p = Node.all().filter('slug = ', slug).get()
    if p is None:
        return u''
    return p.get_absolute_url()


