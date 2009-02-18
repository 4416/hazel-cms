# -*- coding: utf-8 -*-
from wtforms import Form
from wtforms import TextField
from wtforms import SubmitField
from wtforms.validators import regexp

from hazel.models.settings import Settings

from hazel import invalidate_urls

# there is nothing to configure.
defaults = { } 

# we could even overwrite this one,
# FIXME: can we really or are we calling any DataStore related methods
#        on the NutSettings object?
NutSettings = lambda : Settings.get_or_create('settings:files', **defaults)

import views

__all__ = ['NutSettings']
