# -*- coding: utf-8 -*-
import sys
import re
from glob import glob
from os import path
from usersettings import ALLOWED_HOSTS
from logging import info
################################################################################
# import the libraries
################################################################################
root_path = path.abspath(path.dirname(__file__))

# google zipimport lags for some strange reason!
#libz      = glob(path.join(root_path, 'libz', '*.zip'))
#for lib in libz:
#        sys.path.insert(0,lib)
sys.path.insert(0, path.join(root_path, 'lib'))

################################################################################
# imports
################################################################################
from google.appengine.ext.webapp.util import run_wsgi_app
from werkzeug import responder, redirect
from werkzeug import Local, LocalManager
from utils import manager, local
from utils import Request
from urls import url_map, views

################################################################################
# regular expressions
################################################################################
rx = '(?P<protocol>https?://)(?P<host>[^:/]+):?(?P<post>[^/]*)(?P<query>.*)'
rxc = re.compile(rx)

################################################################################
# DebuggedApplication Decorator
################################################################################
import os, sys
def debugged(app):
    if 'SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'].startswith('Dev'):
        # use our debug.utils with Jinja2 templates
        import debug.utils
        sys.modules['werkzeug.debug.utils'] = debug.utils

        # don't use inspect.getsourcefile because the imp module is empty
        import inspect
        inspect.getsourcefile = inspect.getfile

        # wrap the application
        from werkzeug import DebuggedApplication
        app = DebuggedApplication(app, evalex=True)
    return app

################################################################################
# application
################################################################################
@debugged
@manager.middleware
@responder
def application(environ, start_response):
    local.request = request = Request(environ)
    m = rxc.match(request.url)
    m = m.groupdict()
    if m['host'] not in ALLOWED_HOSTS:
        redir = '%s%s%s' % (m['protocol'], ALLOWED_HOSTS[0], m['query'])
        return redirect(redir)
    response = None

    local.adapter = adapter = url_map.bind_to_environ(environ)
    response = adapter.dispatch(lambda e, v: views[e](request, **v),
                                                                catch_http_exceptions=True)

    return response

################################################################################
# initiation
################################################################################
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
