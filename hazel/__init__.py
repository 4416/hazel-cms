# -*- coding: utf-8 -*-
import re

from google.appengine.api import memcache

from jinja2 import Environment

from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms import IntegerField

CACHE_KEY_URL = 'hazel:urls'
admin_tabs = {}

#TODO: 
#      - missing imports
#      - how to populate the form control with the adsense data?


class CSVField(TextField):
    """Quick and dirty CSV field for editing lists of strings.
    Should work in wtforms 0.3 and 0.4."""
    def _value(self):
        return ', '.join([unicode(x) for x in self.data])

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [v.strip() for v in valuelist[0].split(',') if v.strip()]
        else:
            self.data = []


from models.settings import Settings

defaults = { 'nuts': ['pages', 'articles'],
             'admins': ['Nobody <nobody@localhost>',],
             'hosts': ['localhost', 'appspot.com'],
             'google_analytics' : '',
             'google_adsense_client' : '',
             'google_adsense_slot' : '',
             'google_adsense_width': 0,
             'google_adsense_height': 0,
             'disqus_forum' : '' }
NutSettings = lambda : Settings.get_or_create('settings:hazel', **defaults)

class SettingsForm(Form):
    nuts = CSVField('Nuts', [], u'A list of your activated modules')
    # FIXME: create a custom validator that does the validation of the
    #        Name <Email>[, Name <Email>]* field.
    admins = CSVField('Admins', [], u'A list of people who will be notified in case of emergency')
    hosts = CSVField('Hosts', [], u'A comma seperated list of hosts on which to listen. In case of a unknown host, a redirect to the first item in the list will occour.')
    # FIXME: create validator
    google_analytics = TextField('Google Analytics ID', [], u'UA-xxxxxx-xx')
    google_adsense_client = TextField('Google AdSense Client', [], u'pub-...')
    google_adsense_slot   = TextField('Google AdSense Slot', [], u'the slot value')
    google_adsense_width  = IntegerField('Google AdSense Width', [], u'the width value')
    google_adsense_height = IntegerField('Google AdSense Height', [], u'the height value')
    disqus_forum          = TextField('Disqus Forum ID', [], u'The name of the disqus forum to use for comments')
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

def invalidate_urls():
    # caching temporarily disabled
    pass
#    memcache.delete(CACHE_KEY_URL)

jinja_env = Environment(extensions=['jinja2.ext.do'])
layout_env = Environment()

__all__ = ('jinja_env', 'layout_env')
