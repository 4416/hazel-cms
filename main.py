# -*- coding: utf-8 -*-
import sys
import re
from glob import glob
from os import path
from logging import info


################################################################################
# import the libraries
################################################################################
root_path = path.abspath(path.dirname(__file__))
sys.path.insert(0, path.join(root_path, 'lib'))
base_path = path.join(root_path, 'hazel')

################################################################################
# imports
################################################################################
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users

from werkzeug import responder
from werkzeug import redirect
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from jinja2 import Environment
from jinja2 import FileSystemLoader

from hazel.util import manager
from hazel.util import local
from hazel.util.net import Request
from hazel.util.decorators import debugged
from hazel.util.decorators import jinja_const
from hazel.util.decorators import layout_const
from hazel.util.constants import file_ext_to_content_type
from hazel.util.constants import content_type_to_file_ext
from hazel.util import filter

from hazel.urls import build_urls

from hazel.loader import LayoutLoader
from hazel import jinja_env
from hazel import layout_env

from hazel import NutSettings as AppSettings

################################################################################
# globals
################################################################################
rx = '(?P<protocol>https?://)(?P<host>[^:/]+):?(?P<post>[^/]*)(?P<query>.*)'
rxc = re.compile(rx)

__app__ = jinja_const('app', "Hazel CMS")
__version__ = jinja_const('version', "0.1")
__author__ = jinja_const('author', "Moritz Angermann <moritz.angermann@gmail.com>")
__copyright__ = jinja_const('copyright', "Copyright (c) 2008-2009, Moritz Angermann")
__license__ = jinja_const('license', "BSD License")
__URL__ = jinja_const('url', "http://www.hazel-cms.com")
jinja_const('ct2fe', content_type_to_file_ext)
jinja_const('fe2ct', file_ext_to_content_type)
jinja_const('google_users', users)

################################################################################
# application
################################################################################
@debugged
@manager.middleware
@responder
def application(environ, start_response):
    local.request = request = Request(environ)
    settings = AppSettings()
    m = rxc.match(request.url)
    m = m.groupdict()
    if not any([m['host'].endswith(h) for h in settings.hosts]):
        redir = '%s%s%s' % (m['protocol'], settings.hosts[0], m['query'])
        return redirect(redir)
    response = None
    layout_const('app_settings', jinja_const('app_settings', settings))
    for nut in settings.nuts:
        ns = getattr(__import__('hazel.nuts.%s' % nut, \
                                fromlist=['hazel.nuts']), 'NutSettings', None)
        if ns:
            ns = ns()
            layout_const('%s_settings' % nut, ns)
            jinja_const('%s_settings' % nut, ns)

    local.adapter = adapter = local.url_map.bind_to_environ(environ)
    try:
        local.endpoint, local.args = endpoint, args = adapter.match()
        res = local.views[endpoint](request, **args)
        return res
    except HTTPException, e:
        return e(environ, start_response)
    except Exception, e:
        info(e)
        return NotFound()


################################################################################
# initiation
################################################################################
def main():
    appSettings = AppSettings()
    template_paths = [path.join(base_path, 'templates')]\
                   + [path.join(base_path, 'nuts', nut, 'templates')\
                      for nut in appSettings.nuts]
    jinja_env.loader=FileSystemLoader(template_paths)
    layout_env.loader=LayoutLoader()
    # at this point all other modules should have been loaded
    local.url_map, local.views = build_urls()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
