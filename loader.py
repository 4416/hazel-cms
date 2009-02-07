# -*- coding: utf-8 -*-
from jinja2 import BaseLoader, TemplateNotFound
from models.pages import Layout

class LayoutLoader(BaseLoader):
    def get_source(self, environment, template):
        layout = Layout.all().filter('name =', template).get()
        if layout is None:
            raise TemplateNotFound(template)
        source = layout.body
        return source, None, lambda: False
