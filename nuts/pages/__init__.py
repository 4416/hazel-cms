# -*- coding: utf-8 -*-
from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import regexp

from models.settings import Settings

from hazel import invalidate_urls

defaults = { 'subdomain': '',
             'submount': '/pages',
             }

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


__all__ = ['NutSettings']
