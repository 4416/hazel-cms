# -*- coding: utf-8 -*-
from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import url
from wtforms.validators import regexp

from hazel.models import Settings
from hazel.util.decorators import jinja_const

from hazel import invalidate_urls

defaults = { 'subdomain': '',
             'submount' : '',
             'title'    : '',
             'subtitle' : '',
             'feedburner_url': '' }

NutSettings = lambda : Settings.get_or_create('settings:articles', **defaults)

def setup():
    jinja_const('articles_settings', NutSettings())

class SettingsForm(Form):
    subdomain = TextField('Subdomain', [regexp(r'^[A-Za-z0-9_-]{0,32}$')], u'This specifies the subdomain on which the pages will listen. An empty value listens on all subdomains.')
    submount = TextField('Submount', [regexp(r'^[A-Za-z0-9_-|/]*$')], u'This specifies the subdirectory where the pages will listen to. An empty value means "/"')
    title = TextField('Title', [], u'This is your Blogs title')
    subtitle = TextField('Subtitle', [], u'This is your Blogs subtitle')
    feedburner_url = TextField('Feedburner URL', [url], u'If you use feedburner to enhance your feed, enter your burned feed url here.')
    save = SubmitField(u'Save')

def handle_form_data(form):
    settings = NutSettings()
    dirty = False
    for attr in defaults.keys():
        if getattr(settings, attr) != getattr(form, attr).data:
            setattr(settings, attr, getattr(form, attr).data)
            dirty = True
    if dirty:
        settings.put()
        invalidate_urls()

import views
import feeds

__all__ = ['NutSettings']
