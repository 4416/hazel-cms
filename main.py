# -*- coding: utf-8 -*-
import sys
import re
from glob import glob
from os import path
from usersettings import ALLOWED_HOSTS
from logging import info
import os, sys


################################################################################
# import the libraries
################################################################################
root_path = path.abspath(path.dirname(__file__))
sys.path.insert(0, path.join(root_path, 'lib'))

################################################################################
# imports
################################################################################
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users

from werkzeug import responder
from werkzeug import redirect
from jinja2 import Environment
from jinja2 import FileSystemLoader

from util.manage import manager
from util.manage import local
from util.net import Request
from util.decorators import update_environment
from util.decorators import debugged
from util.decorators import jinja_const
from util.constants import file_ext_to_content_type
from util.constants import content_type_to_file_ext
from util import filter

from urls import url_map
from urls import views

from loader import LayoutLoader

################################################################################
# globals
################################################################################
rx = '(?P<protocol>https?://)(?P<host>[^:/]+):?(?P<post>[^/]*)(?P<query>.*)'
rxc = re.compile(rx)

TEMPLATE_PATH = path.join(path.dirname(__file__), 'templates')

__app__ = jinja_const('app', "Hazel CMS")
__version__ = jinja_const('version', "0.1")
__author__ = jinja_const('author', "Moritz Angermann <moritz.angermann@gmail.com>")
__copyright__ = jinja_const('copyright', "Copyright (c) 2008-2009, Moritz Angermann")
__license__ = jinja_const('license', "BSD License")
__URL__ = jinja_const('url', "http://www.hazel-cms.com")
jinja_const('ct2fe', content_type_to_file_ext)
jinja_const('fe2ct', file_ext_to_content_type)
jinja_const('google_users', users)

# FIXME:
jinja_const('feedburner_id', 'journal-ma')
jinja_const('disqus_forum', 'devjma')

import usersettings as us
us.AUTHOR, us.AUTHOR_EMAIL = us.ADMINS[0]
us.SNAIL_ADDRESS = us.AUTHOR_SNAIL
jinja_const('SETTINGS', us)
# END FIXME


################################################################################
# application
################################################################################
@debugged
@manager.middleware
@responder
def application(environ, start_response):
    local.request = request = jinja_const('request', Request(environ) )
    m = rxc.match(request.url)
    m = m.groupdict()
    if m['host'] not in ALLOWED_HOSTS:
        redir = '%s%s%s' % (m['protocol'], ALLOWED_HOSTS[0], m['query'])
        return redirect(redir)
    response = None
    update_environment()
    local.adapter = adapter = url_map.bind_to_environ(environ)
    response = adapter.dispatch(lambda e, v: views[e](request, **v),
                                catch_http_exceptions=True)

    return response

################################################################################
# initiation
################################################################################
def main():
    local.jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH),
                                  extensions=['jinja2.ext.do'])
    local.layout_env = Environment(loader=LayoutLoader())
    # at this point all other modules should have been loaded
    update_environment();
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
