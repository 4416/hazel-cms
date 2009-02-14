# -*- coding: utf-8 -*-
from models import Settings
defaults = { 'nuts': ['pages', 'articles'] }
settings = Settings.get_or_create('settings:hazel', **defaults)
