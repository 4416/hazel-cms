# -*- coding: utf-8 -*-
from os import path
from jinja2 import Environment, FileSystemLoader
from werkzeug import Local, LocalManager
from werkzeug import BaseRequest, AcceptMixin, ETagRequestMixin
from werkzeug import BaseResponse, ETagResponseMixin, ResponseStreamMixin, CommonResponseDescriptorsMixin
from werkzeug.routing import Map, Rule

from datetime import datetime, timedelta

from util.tools import slugify, simple_rec

from loader import LayoutLoader

from models.pages import Node, PUBLISHED

from google.appengine.api import memcache

################################################################################
# Classes
################################################################################

class Request(BaseRequest, AcceptMixin, ETagRequestMixin):
    pass

class Response(BaseResponse, ETagResponseMixin, ResponseStreamMixin, CommonResponseDescriptorsMixin):
    pass


################################################################################
# Local (Request Global Variable) handling
################################################################################
local = Local()
manager = LocalManager([local])


################################################################################
# Decorator
################################################################################
# memcache decorator
def memcached(fn):
    def _fn(request, *args, **kwargs):
        key = request.path
        resp = memcache.get(key)
        if resp is not None:
            return resp
        resp = fn(request, *args, **kwargs)
    if resp.prevent_cache:
        return resp
            resp.expires = datetime.now() + timedelta(7)
            memcache.add(key, resp)
            return resp
    return _fn

################################################################################
# Globals
################################################################################
file_ext_to_content_type = { 'jpg': 'image/jpeg',
                                                         'gif': 'image/gif',
                                                         'css': 'text/css',
                                                         'txt': 'text/plain',
                                                         'png': 'image/png',
                                                         'xml': 'text/xml',
                                                         'js' : 'application/x-javascript',
                                                         'html': 'text/html' }
content_type_to_file_ext = dict([(v,k) for k,v in file_ext_to_content_type.items()])


TEMPLATE_PATH = path.join(path.dirname(__file__), 'templates')

def url_for(endpoint, _external=False, **values):
    url = local.adapter.build(endpoint, values, force_external=_external)
    if url.startswith(u'/'):
        return url
    return u'/' + url

def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')

def render_jinja(template, **context):
    return jinja_env.get_template(template).render(**context)

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), extensions=['jinja2.ext.do'])
jinja_env.globals['url_for'] = url_for
jinja_env.filters['slugify'] = slugify
jinja_env.globals['request'] = lambda: local.request
jinja_env.globals['ct2fe'] = content_type_to_file_ext


def menu(root='root'):
    base = Node.all().filter('name = ', root).get()
    qs = Node.all().filter('active = ', True).filter('state = ', PUBLISHED)
    l = len(base.path)
    nodes = dict([(n.get_key(), n) for n in qs if n.path.startswith(base.path)])

    node = simple_rec(base, nodes)
    info(node)
    return node

################################################################################
# Layout renderer
from models.pages import File
def file_path(slug):
    f = File.all().filter('slug = ', slug).get()
    if f is None:
        return u''
    return u'/file/%s.%s' % (f.slug, content_type_to_file_ext[f.content_type])


layout_env = Environment(loader=LayoutLoader())
layout_env.globals['file'] = file_path
layout_env.globals['menu'] = menu


def render_layout(layout, **context):
    return layout_env.get_template(layout).render(**context)

def render_layout_from_string(string, **context):
    return layout_env.from_string(string).render(**context)

def layout_response_from_string(string, content_type='text/html', **context):
    return Response(render_layout_from_string(string, **context), mimetype=content_type)
################################################################################

from google.appengine.api import users
jinja_env.globals['google_users'] = users
jinja_env.globals['feedburner_id'] = 'journal-ma'
jinja_env.globals['disqus_forum'] = 'devjma'

import usersettings as us
us.AUTHOR, us.AUTHOR_EMAIL = us.ADMINS[0]
us.SNAIL_ADDRESS = us.AUTHOR_SNAIL
jinja_env.globals['SETTINGS'] = us

def layout_filter(fn):
    layout_env.filters[fn.__name__] = fn
    return fn

def jinja_filter(fn):
    jinja_env.filters[fn.__name__] = fn
    return fn

from logging import info

################################################################################
# view utils
################################################################################
def pager(qs, qs_asc, qs_desc, per_page=10, bookmark=None):
    """compiles a list of entities and signals if a next
       or prev selection exist for the given query"""

    # macro
    def fetcher(qs):
        """fetches ``per_page+1`` entities,
           return ``per_page`` entities and
           a flag indicating if more entities exist"""
        more = False
        e = qs.fetch(per_page+1)
        if len(e) == per_page+1:
            more = True
            e = e[:per_page]
        return (e, more)

    # At initiation the assumtion is that we can display all
    # entities returned from the queryset ``qs``.

    prev = None
    next = None

    # based on the ``bookmark`` we fetch the entities from
    # the datastore. If the ``bookmark`` is not None we
    # assume that a page in the opposite paging direction
    # exists.

    if bookmark is None:
        entities, next = fetcher(qs)
    else:
        if not bookmark.startswith('-'):
            prev = True
            entities, next = fetcher(qs_asc(bookmark))
        else:
            next = True
            entities, prev = fetcher(qs_desc(bookmark[1:]))
            entities.reverse()
    return (prev, entities, next)

################################################################################
# Custom Filters
################################################################################
## datetimeformat
@jinja_filter
def date(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

## markdown
@jinja_filter
@layout_filter
def markdown(text,*args):
    try:
        import markdown2
    except ImportError:
        info("Error in `markdown` filter: The Python markdown2 library isn't installed.")
        return text
    return markdown2.markdown(text,extras=args)

## truncatewords (from django)
@jinja_filter
def truncatewords(text, num=10):
    words = text.split()
    if len(words) <= num:
        return text
    words = words[:num]
    if not words[-1].endswith('...'):
        words.append('...')
    return u' '.join(words)

## striptags (from django)
@jinja_filter
def striptags(text):
    return re.sub(r'<[^>]*?>', '', text)

################################################################################
# Typogirfy Filters // Quick hack
################################################################################
import re
## amp
@layout_filter
@jinja_filter
def amp(text):
    tag_pattern = '</?\w+((\s+\w+(\s*=\s*(?:".*?"|\'.*?\'|[^\'">\s]+))?)+\s*|\s*)/?>'
    amp_finder = re.compile(r"(\s|&nbsp;)(&|&amp;|&\#38;)(\s|&nbsp;)")
    intra_tag_finder = re.compile(r'(?P<prefix>(%s)?)(?P<text>([^<]*))(?P<suffix>(%s)?)' % (tag_pattern, tag_pattern))
    def _amp_process(groups):
        prefix = groups.group('prefix') or ''
        text = amp_finder.sub(r"""\1<span class="amp">&amp;</span>\3""", groups.group('text'))
        suffix = groups.group('suffix') or ''
        return prefix + text + suffix
    output = intra_tag_finder.sub(_amp_process, text)
    return output

## caps
@layout_filter
@jinja_filter
def caps(text):
    try:
        import smartypants
    except ImportError:
        info("Error in `caps` filter: The Python SmartyPants library isn't installed.")
        return text

    tokens = smartypants._tokenize(text)
    result = []
    in_skipped_tag = False

    cap_finder = re.compile(r"""(
                            (\b[A-Z\d]*        # Group 2: Any amount of caps and digits
                            [A-Z]\d*[A-Z]      # A cap string much at least include two caps (but they can have digits between them)
                            [A-Z\d']*\b)       # Any amount of caps and digits or dumb apostsrophes
                            | (\b[A-Z]+\.\s?   # OR: Group 3: Some caps, followed by a '.' and an optional space
                            (?:[A-Z]+\.\s?)+)  # Followed by the same thing at least once more
                            (?:\s|\b|$))
                            """, re.VERBOSE)

    def _cap_wrapper(matchobj):
        """This is necessary to keep dotted cap strings to pick up extra spaces"""
        if matchobj.group(2):
            return """<span class="caps">%s</span>""" % matchobj.group(2)
        else:
            if matchobj.group(3)[-1] == " ":
                caps = matchobj.group(3)[:-1]
                tail = ' '
            else:
                caps = matchobj.group(3)
                tail = ''
            return """<span class="caps">%s</span>%s""" % (caps, tail)

    tags_to_skip_regex = re.compile("<(/)?(?:pre|code|kbd|script|math)[^>]*>", re.IGNORECASE)


    for token in tokens:
        if token[0] == "tag":
            # Don't mess with tags.
            result.append(token[1])
            close_match = tags_to_skip_regex.match(token[1])
            if close_match and close_match.group(1) == None:
                in_skipped_tag = True
            else:
                in_skipped_tag = False
        else:
            if in_skipped_tag:
                result.append(token[1])
            else:
                result.append(cap_finder.sub(_cap_wrapper, token[1]))
    output = "".join(result)
    return output

## initial_quotes
@layout_filter
@jinja_filter
def initial_quotes(text):
    quote_finder = re.compile(r"""((<(p|h[1-6]|li|dt|dd)[^>]*>|^)              # start with an opening p, h1-6, li, dd, dt or the start of the string
                                  \s*                                          # optional white space!
                                  (<(a|em|span|strong|i|b)[^>]*>\s*)*)         # optional opening inline tags, with more optional white space for each.
                                  (("|&ldquo;|&\#8220;)|('|&lsquo;|&\#8216;))  # Find me a quote! (only need to find the left quotes and the primes)
                                                                               # double quotes are in group 7, singles in group 8
                                  """, re.VERBOSE)
    def _quote_wrapper(matchobj):
        if matchobj.group(7):
            classname = "dquo"
            quote = matchobj.group(7)
        else:
            classname = "quo"
            quote = matchobj.group(8)
        return """%s<span class="%s">%s</span>""" % (matchobj.group(1), classname, quote)
    output = quote_finder.sub(_quote_wrapper, text)
    return text

## smartypants
@layout_filter
@jinja_filter
def smartypants(text):
    try:
        import smartypants
    except ImportError:
        info("Error in `smartypants` filter: The Python smartypants library isn't installed.")
        return text
    else:
        output = smartypants.smartyPants(text)
        return output

## titlecase
@layout_filter
@jinja_filter
def titlecase(text):
    text = force_unicode(text)
    try:
        import titlecase
    except ImportError:
        info("Error in {% titlecase %} filter: The titlecase.py library isn't installed.")
        return text
    else:
        return titlecase.titlecase(text)

## widont
@layout_filter
@jinja_filter
def widont(text):
    widont_finder = re.compile(r"""((?:</?(?:a|em|span|strong|i|b)[^>]*>)|[^<>\s]) # must be proceeded by an approved inline opening or closing tag or a nontag/nonspace
                                   \s+                                             # the space to replace
                                   ([^<>\s]+                                       # must be flollowed by non-tag non-space characters
                                   \s*                                             # optional white space!
                                   (</(a|em|span|strong|i|b)>\s*)*                 # optional closing inline tags with optional white space after each
                                   ((</(p|h[1-6]|li|dt|dd)>)|$))                   # end with a closing p, h1-6, li or the end of the string
                                   """, re.VERBOSE)
    output = widont_finder.sub(r'\1&nbsp;\2', text)
    return output

## typogrify
@layout_filter
@jinja_filter
def typogrify(text):
    text = amp(text)
    text = widont(text)
    text = smartypants(text)
    text = caps(text)
    text = initial_quotes(text)
    return text
