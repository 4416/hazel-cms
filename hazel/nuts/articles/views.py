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
from hazel.admin.forms import ArticleForm

from urls import expose, expose_admin
from models import Post
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
def index(request):
    latest = Post.pub().get()
    if latest:
        return redirect(quote((u'/%s' % latest.lookup).encode('utf-8')), 301)
    return render_template('empty.html')

@expose('/<path:key>')
@memcached
def show(request, key):
    prevent_cache = False
    post = Post.get_by_key_name('Published:%s' % key)
    if not post and users.is_current_user_admin():
        # admin might also try to retrieve the post by it's key!
        post = Post.get_by_key_name(key)
        prevent_cache = True
    if post:
        resp = render_template('articles/show.html', post=post)
        resp.prevent_cache = prevent_cache
    else:
        resp = render_template('404.html')
        resp.prevent_cache = True
    return resp

@expose('/archive/', defaults={ 'tag': None })
@expose('/topic/<tag>/')
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
    return render_template('post_list.html',
                           prev=prev, next=next,
                           posts = posts,
                           tag=tag)

################################################################################
# Admin views
@expose_admin('/list/', tab='Articles')
def list(request):
    from logging import info
    from datetime import datetime
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
    return render_template('articles/list.html',
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
            return render_template('articles/form.html', form=form, status='error',msg='non-unique')
        return redirect(url_for('nut:articles/list'), 301)
    return render_template('articles/form.html', form=form)

@expose_admin('/edit/<key>/')
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
    return render_template('articles/form.html', form=form, post=post, status=status)

@expose_admin('/delete/<key>/')
def delete(request, key):
    post = Post.get_by_key_name(key)
    if request.method == 'POST':
        post.delete()
        return redirect(url_for('nut:articles/list'), 301)
    return render_template('post_confirm_delete.html', post=post)
