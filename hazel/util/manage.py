# -*- coding: utf-8 -*-
from werkzeug import Local, LocalManager

local = Local()
manager = LocalManager([local])
