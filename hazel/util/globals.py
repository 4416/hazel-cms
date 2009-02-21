# -*- coding: utf-8 -*-
from hazel.util import local
from decorators import jinja_global
from werkzeug import url_quote_plus

@jinja_global
def url_for(endpoint, _external=False, _anchor=None, **values):
    url = local.adapter.build(endpoint, values, force_external=_external)
    if _anchor is not None:
        url += '#' + url_quote_plus(_anchor)
    if url.startswith(u'/') or url.startswith(u'http'):
        return url
    return u'/' + url
