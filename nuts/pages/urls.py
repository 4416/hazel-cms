# -*- coding: utf-8 -*-
from werkzeug.routing import Rule
from werkzeug.routing import Submount
from werkzeug.routing import Subdomain

from . import NutSettings


def build_rules():
    settings = NutSettings()
    rules = [
        Rule('/', defaults={'key':''}, endpoint='show'),
        Rule('/<path:key>', endpoint='show'),
        ]
    if settings.submount:
        rules = [Submount(settings.submount, rules)]
    if settings.subdomain:
        rules = [Subdomain(settings.subdomain, rules)]
    return rules
