# -*- coding: utf-8 -*-
from werkzeug import Local
from werkzeug import LocalManager
from jinja2 import Environment

local = Local()
manager = LocalManager([local])

__all__ = ('local', 'manager')
