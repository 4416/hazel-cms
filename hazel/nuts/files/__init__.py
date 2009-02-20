# -*- coding: utf-8 -*-
"""The file nut allows you to upload static media to you system. It also contains a convinient method to link to the files in you shelf, which will always point to the right url."""

__title__ = "Filebox"
__version__ = 0.5
__admin__ = "nut:files/list"

from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import regexp

from hazel.models.settings import Settings

from hazel import invalidate_urls
from hazel.util.decorators import layout_global

from models import File

# there is nothing to configure.
defaults = { } 

# we could even overwrite this one,
# FIXME: can we really or are we calling any DataStore related methods
#        on the NutSettings object?
NutSettings = lambda : Settings.get_or_create('settings:files', **defaults)

@layout_global('file')
def file_path(slug):
    f = File.all().filter('abs_path = ', slug).get()
    if f is None:
        f = File.all().filter('slug = ', slug).get()
    if f is None:
        return u''
    return f.get_absolute_url()


import views

__all__ = ['NutSettings']
