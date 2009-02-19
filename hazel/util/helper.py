# -*- coding: utf-8 -*-
from hazel.util import local
from net import Response
from hazel import jinja_env
from hazel import layout_env

def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(request=local.request,
                                                                  **context),
                    mimetype='text/html')

def render_jinja(template, **context):
    return jinja_env.get_template(template).render(request=local.request,
                                                         **context)

def render_layout(layout, **context):
    return layout_env.get_template(layout).render(request=local.request,
                                                        **context)

def render_layout_from_string(string, **context):
    return layout_env.from_string(string).render(request=local.request,
                                                       **context)

def layout_response_from_string(string, content_type='text/html', **context):
    return Response(render_layout_from_string(string, **context), mimetype=content_type)
