# -*- coding: utf-8 -*-
from hazel.util import local
from decorators import jinja_global

@jinja_global
def url_for(endpoint, _external=False, **values):
    url = local.adapter.build(endpoint, values, force_external=_external)
    if url.startswith(u'/') or url.startswith(u'http'):
        return url
    return u'/' + url
