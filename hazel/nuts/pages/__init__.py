# -*- coding: utf-8 -*-
"""The pages nut enables you a rich set of layout and page options."""

__title__ = "Pages with layouts"
__version__ = 0.2
__admin__ = "nut:pages/list_pages"

from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import regexp

from hazel.models.settings import Settings

from hazel.util.tools import simple_rec
from hazel.util.decorators import jinja_global
from hazel.util.decorators import layout_global
from hazel import invalidate_urls

from models import Node
from models import PUBLISHED

defaults = { 'subdomain': '',
             'submount': '/pages' }

NutSettings = lambda : Settings.get_or_create('settings:pages', **defaults)

class SettingsForm(Form):
    subdomain = TextField('Subdomain', [regexp(r'^[A-Za-z0-9_-]{0,32}$')], u'This specifies the subdomain on which the pages will listen. An empty value listens on all subdomains.')
    submount = TextField('Submount', [regexp(r'^[A-Za-z0-9_-|/]*$')], u'This specifies the subdirectory where the pages will listen to. An empty value means "/"')
    save = SubmitField(u'Save')


def handle_form_data(form):
    settings = NutSettings()
    dirty = False
    if settings.subdomain != form.subdomain.data:
        dirty = True
        settings.subdomain = form.subdomain.data
    if settings.submount != form.submount.data:
        settings.submount = form.submount.data
        dirty = True
    if dirty:
        settings.put()
        invalidate_urls()


################################################################################
# exposed functions
@layout_global
@jinja_global
def menu(abs_path=''):
    base = Node.all().filter('abs_path = ', abs_path).get()
    qs = Node.all().filter('active = ', True).filter('state = ', PUBLISHED)
    l = len(base.abs_path)
    nodes = dict([(n.get_key(), n) for n in qs if n.abs_path.startswith(base.abs_path)])
    node = simple_rec(base, nodes)
    return node

@layout_global
@jinja_global
def page_list(abs_path=''):
    base = Node.all().filter('abs_path = ', abs_path).get()
    if base:
        return Node.get(base.children)
    else:
        return None

@layout_global('page')
def page_path(slug, **kwargs):
    p = Node.all().filter('abs_path = ', slug).get()
    if p is None:
        p = Node.all().filter('slug = ', slug).get()
    if p is None:
        return u''
    return p.get_absolute_url(**kwargs)

import views

__all__ = ['NutSettings']
