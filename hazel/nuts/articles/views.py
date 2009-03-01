# -*- coding: utf-8 -*-
from datetime import datetime
from logging import info
from logging import debug
from urllib2 import quote

from google.appengine.api import users
from google.appengine.ext.db import run_in_transaction, TransactionFailedError

from werkzeug import redirect

from hazel.util.helper import render_template
from hazel.util.helper import render_jinja
from hazel.util.net import Response
from hazel.util.tools import pager
from hazel.util.tools import slugify
from hazel.util.decorators import memcached
from hazel.util.decorators import memcached_for
from hazel.admin.forms import ArticleForm
from hazel.util.globals import url_for

from urls import expose, expose_admin
from models import Post
from . import NutSettings

################################################################################
# constants
################################################################################
COPY_ATTR = 'title,city,country,published,pub_date,body'.split(',')

################################################################################
# utilities
################################################################################


def prepare(form):
    """
    prepared the form data for the model
    """
    data = dict([(attr,getattr(form,attr).data) for attr in COPY_ATTR])
    data['topics'] = [tag.strip() for tag in form.topics.data.split(',')]
    data['slug']   = slugify(data['title'])
    dt = data['pub_date']
    if not dt:
        dt = datetime.now()
    data['lookup'] = u'%4d/%02d/%02d/%s' % \
                     (dt.year, dt.month, dt.day, data['slug'])
    data['sort_key'] = u'%s:%s' % (dt.strftime('%Y%m%d%H%M%S'),
                                   data['slug'])
    if data['published']:
        key_name = u'Published:%s' % data['lookup']
    else:
        key_name = u'Post:%s' % data['lookup']
    return key_name, data

class PostProxy(object):
    """
    wrapper for the WTForm object on existing models
    """
    def __init__(self, post):
        for attr in COPY_ATTR:
            setattr(self,attr,getattr(post,attr))
        self.topics = ', '.join(post.topics)

class AutoNow(object):
    """
    wrapper to initialize an empty form with the current time
    """
    def __init__(self):
        self.pub_date = datetime.now()

################################################################################
# transactions
################################################################################

def create_entity(key_name, **kwds):
    def tnx():
        entity = Post.get_by_key_name(key_name)
        if entity is None:
            entity = Post(key_name=key_name, **kwds)
            entity.put()
            return (True, entity)
        return (False, entity)
    return run_in_transaction(tnx)

def update_entity(key_name, **kwds):
    def tnx():
        entity = Post.get_by_key_name(key_name)
        for key, value in kwds.items():
            setattr(entity, key, value)
        entity.put()
        return entity
    return run_in_transaction(tnx)

################################################################################
# the views
################################################################################x

@expose('/')
@memcached_for('15m')
def index(request):
    latest = Post.pub().fetch(5)
    # latest.reverse()
    ns = NutSettings()
    template = ns.index_layout
    if template:
        template = 'nut:layout/%s' % template
    else:
        template = 'app:articles/index.html'
    return render_template(template, posts=latest)
    latest = Post.pub().get()
    if latest:
        return redirect(quote((u'/%s' % latest.lookup).encode('utf-8')), 301)
    return render_template('app/empty.html')

@expose('/<path:key>')
@memcached_for('15m')
def show(request, key):
    prevent_cache = False
    post = Post.get_by_key_name('Published:%s' % key)
    if not post and users.is_current_user_admin():
        # admin might also try to retrieve the post by it's key!
        post = Post.get_by_key_name(key)
        prevent_cache = True
    if post:
        ns = NutSettings()
        template = ns.articles_layout
        if template:
            template = 'nut:layout/%s' % template
        else:
            template = 'app:articles/show.html'
        resp = render_template(template, post=post)
        resp.prevent_cache = prevent_cache
    else:
        resp = render_template('app/404.html')
        resp.prevent_cache = True
    return resp

@expose('/search/')
@memcached_for('15m')
def search(request):
    ns = NutSettings()
    template = ns.search_layout
    if template:
        template = 'nut:layout/%s' % template
    else:
        template = 'app:articles/search.html'
    return render_template(template)

@expose('/archive/', defaults={ 'tag': None })
@expose('/topic/<tag>/')
@memcached_for('15m')
def topic(request, tag):
    qs = Post.pub()
    rqs = Post.rpub()
    if tag is not None:
        qs = qs.filter('topics = ', tag)
        rqs = rqs.filter('topics = ', tag)
    prev, posts, next = pager(qs,
                              lambda bm: qs.filter('sort_key <', bm),
                              lambda bm: rqs.filter('sort_key >', bm),
                              bookmark=request.args.get('bookmark', None))
    ns = NutSettings()
    template = ns.archive_layout
    if template:
        template = 'nut:layout/%s' % template
    else:
        template = 'app:articles/archive.html'    
    return render_template(template,
                           prev=prev, next=next,
                           posts = posts,
                           tag=tag)

################################################################################
# Admin views
@expose_admin('/list/', tab='Articles')
def list(request):
    from logging import info
    from datetime import datetime

    if request.method == 'POST':
        handle_backup(request.files.get('backup'))
    
    pub_bm, upc_bm, unp_bm = None, None, None
    if request.args.get('list','') == 'published':
        pub_bm = request.args.get('bookmark', None)
    elif request.args.get('list','') == 'upcoming':
        upc_bm = request.args.get('bookmark', None)
    elif request.args.get('list','') == 'unpublished':
        unp_bm = request.args.get('bookmark', None)

    pub_prev, pub, pub_next = pager(Post.pub(),
                                   lambda bm: Post.pub().filter('sort_key <', bm),
                                   lambda bm: Post.rpub().filter('sort_key >', bm),
                                    bookmark=pub_bm)
    upc_prev, upc, upc_next = pager(Post.upcoming(),
                                   lambda bm: Post.upcoming()\
                                                  .filter('sort_key <', bm),
                                   lambda bm: Post.rupcoming()\
                                                  .filter('sort_key >', bm),
                                   bookmark=upc_bm)
    unp_prev, unp, unp_next = pager(Post.unpub(),
                                   lambda bm: Post.unpub()\
                                                  .filter('sort_key <', bm),
                                   lambda bm: Post.runpub()\
                                                  .filter('sort_key >', bm),
                                   bookmark=unp_bm)
    return render_template('app:articles/list.html',
                           unpublished_prev = unp_prev,
                           unpublished      = unp,
                           unpublished_next = unp_next,
                           upcoming_prev    = upc_prev,
                           upcoming         = upc,
                           upcoming_next    = upc_next,
                           published_prev   = pub_prev,
                           published        = pub,
                           published_next   = pub_next)

@expose_admin('/add/')
def add(request):
    form = ArticleForm(request.form, obj=AutoNow(), prefix='create')
    if request.method == 'POST' and form.validate():
        key_name, kwds = prepare(form)
        # kwds['html'] = render_jinja('cache_body.html', body=kwds['body'])
        kwds['author'] = users.get_current_user()
        # lets see if we do not overwrite an existing item.
        created, post = create_entity(key_name, **kwds)
        if not created:
            return render_template('app:articles/form.html', form=form, status='error',msg='non-unique')
        return redirect(url_for('nut:articles/list'), 301)
    return render_template('app:articles/form.html', form=form)

@expose_admin('/edit/<path:key>/')
def edit(request, key):
    post = Post.get_by_key_name(key)
    form = ArticleForm(request.form, obj=PostProxy(post), prefix='edit')
    status = False
    if request.method == 'POST' and form.validate():
        key_name, kwds = prepare(form)
#        kwds['html'] = render_jinja('cache_body.html', body=kwds['body'])
        if post.key().name() == key_name:
            post = update_entity(key_name, **kwds)
            status = 'Updated'
        else:
            kwds['author'] = users.get_current_user()
            created, entity = create_entity(key_name, **kwds)
            if not created:
                return Response('sorry, post with that pub_date and title'\
                                    + 'exists already')
            post.invalidate_cache()
            post.delete()
            post = entity
            status = 'Updated'
        post.invalidate_cache()
        if form.save.data:
            return redirect(url_for('nut:articles/list'), 301)
    return render_template('app:articles/form.html', form=form, post=post, status=status)

@expose_admin('/delete/<path:key>/')
def delete(request, key):
    post = Post.get_by_key_name(key)
    if request.method == 'POST':
        post.delete()
        return redirect(url_for('nut:articles/list'), 301)
    return render_template('app:articles/post_confirm_delete.html', post=post)


from hazel.models.restoremap import RestoreMap

from struct import pack
from struct import unpack
from struct import error
from logging import info
from google.appengine.api.datastore import Entity
from pickle import dumps
from pickle import loads
from google.appengine.ext import db
from google.appengine.api import users
from zlib import compress
from zlib import decompress


@expose_admin('/backup/', defaults={'kind': 'hazel.nuts.articles.models.Post'})
def backup(request,kind):
    def encode(x):
        if isinstance(x, db.Model):
            return str(x.key())
        if isinstance(x, users.User):
            return x.email()
        return x
    resp = Response(mimetype="application/python-eval-dump", content_type="application/python-eval-dump")
    module, obj = kind.rsplit('.',1)
    mod = __import__(module, fromlist=[module.rsplit('.',1)])
    model = getattr(mod,obj)
    for p in model.all():
        data = (p.__module__, p.__class__.__name__, str(p.key()), [(x, encode(getattr(p,x))) for x in p.properties() if encode(x) is not None])
        pdata = compress(dumps(data,-1),9)
        resp.stream.write(pack('I',len(pdata)))
        resp.stream.write(pdata)
    return resp    


def handle_backup(f):
    key_map = {}
    def decode(x,y):
        if y is None:
            return y
        if isinstance(x, db.UserProperty):
            return users.User(email=y)
        if isinstance(x, db.ReferenceProperty):
            key = RestoreMap.sink_for_key(y)
            if key:
                return db.Key(key)
            return db.Key(y)
        return y
    while True:
        try:
            (l,) = unpack('I', f.read(4))
            t = loads(decompress(f.read(l)))
            mod = __import__(t[0], fromlist=[t[0]])
            kind = getattr(mod,t[1])
            key = db.Key(t[2])
            kwds = dict([(k,decode(getattr(kind, k), v)) for k,v in t[3]])
            if key.name():
                kwds['key_name'] = key.name()
            obj = kind(**kwds)
            obj.put()
            RestoreMap.create_or_update(str(key), sink=str(obj.key()))
        except error, e:
            break

