# -*- coding: utf-8 -*-
"""The cache(w)nut is very simple in it's nature but great in it's exposure. It gives you detailed information about your cache state and allows you you purge it in case of some stale data."""

__title__ = "Cache(w)nut"
__version__ = 0.3
__admin__ = "nut:cache/list"

from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import regexp

from hazel.models.settings import Settings

from hazel import invalidate_urls
from hazel.util.decorators import layout_global

# there is nothing to configure.
defaults = { } 

# we could even overwrite this one,
# FIXME: can we really or are we calling any DataStore related methods
#        on the NutSettings object?
NutSettings = lambda : Settings.get_or_create('settings:files', **defaults)

import views

__all__ = ['NutSettings']
