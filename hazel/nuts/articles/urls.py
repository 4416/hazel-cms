# -*- coding: utf-8 -*-

from werkzeug.routing import Rule
from werkzeug.routing import Submount
from werkzeug.routing import Subdomain

from . import NutSettings

def build_rules():
    settings = NutSettings()
    rules = [
        Rule('/', endpoint='index'),
        Rule('/<path:key>', endpoint='show'),
        Rule('/topic/<tag>/', endpoint='topic'),
        Rule('/archive/', endpoint='archive')
        ]
    if settings.submount:
        rules = [Submount(settings.submount, rules)]
    if settings.subdomain:
        rules = [Subdomain(settings.subdomain, rules)]
    return rules
