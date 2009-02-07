# -*- coding: utf-8 -*-
from utils import layout_response_from_string, memcached
from models.pages import Node, PAGE
from google.appengine.api import memcache
from datetime import datetime, timedelta

@memcached
def show(request, key):
    # eventually the key should be the "abs_path"
    page = Node.all().filter('type =', PAGE).filter('slug = ', key).get()
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
