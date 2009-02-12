# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta

from google.appengine.api import memcache

from util.helper import layout_response_from_string
from util.decorators import memcached
from models.pages import Node, PAGE

@memcached
def show(request, key):
    # eventually the key should be the "abs_path"
    page = Node.all().filter('type =', PAGE).filter('abs_path = ', key).get()
    if page is None:
        raise Exception("Page not found")
    if page.layout is None:
        raise Exception("invalid layout")
    string = [
            "{%% extends '%s' %%}" % page.layout.name,
            "{%% block body %%} %s {%% endblock %%}" % page.body ]
    for block in page.blocks:
        string.append("{%% block %s %%} %s {%% endblock %%}" % (block.name, block.body))
    resp = layout_response_from_string('\n'.join(string), page.content_type, title=page.name)
    resp.expires = datetime.now() + timedelta(7)
    return resp
