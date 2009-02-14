# -*- coding: utf-8 -*-
from manage import local
from net import Response

def render_template(template, **context):
    return Response(local.jinja_env.get_template(template).render(**context),
                    mimetype='text/html')

def render_jinja(template, **context):
    return local.jinja_env.get_template(template).render(**context)

def render_layout(layout, **context):
    return local.layout_env.get_template(layout).render(**context)

def render_layout_from_string(string, **context):
    return local.layout_env.from_string(string).render(**context)

def layout_response_from_string(string, content_type='text/html', **context):
    return Response(render_layout_from_string(string, **context), mimetype=content_type)
