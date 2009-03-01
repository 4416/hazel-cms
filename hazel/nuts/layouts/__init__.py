# -*- coding: utf-8 -*-
"""The layouts nut gives you powerful layouts."""

__title__ = "Layouts"
__version__ = 0.2
__admin__ = "nut:layouts/list"

from wtforms.validators import regexp

from hazel.models.settings import Settings

from hazel.util.tools import simple_rec
from hazel.util.decorators import jinja_global
from hazel.util.decorators import layout_global
from hazel import invalidate_urls

defaults = { }

NutSettings = lambda : Settings.get_or_create('settings:layouts', **defaults)

import views

__all__ = ['NutSettings']
