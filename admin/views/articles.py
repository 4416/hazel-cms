# -*- coding: utf-8 -*-
from utils import render_template, render_jinja, Response, pager
from util.tools import slugify
from logging import info, debug
from models.blog import Post
from datetime import datetime
from werkzeug import redirect

from admin.forms import ArticleForm

from google.appengine.api import users
from google.appengine.ext.db import run_in_transaction, TransactionFailedError

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
# decorator
################################################################################
def require_admin(fn):
    def _fn(request, *args, **kwargs):
        from google.appengine.api import users
        if not users.is_current_user_admin():
            return render_template('no_access.html',request=request)
        return fn(request, *args, **kwargs)
    return _fn


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

def add(request):
    form = ArticleForm(request.form, obj=AutoNow(), prefix='create')
    if request.method == 'POST' and form.validate():
        key_name, kwds = prepare(form)
        kwds['html'] = render_jinja('cache_body.html', body=kwds['body'])
        kwds['author'] = users.get_current_user()
        # lets see if we do not overwrite an existing item.
        created, post = create_entity(key_name, **kwds)
        if not created:
            return render_template('articles/form.html', form=form, status='error',msg='non-unique')
        return redirect('/admin/articles/', 301)
    return render_template('articles/form.html', form=form)

def edit(request, key):
    post = Post.get_by_key_name(key)
    form = ArticleForm(request.form, obj=PostProxy(post), prefix='edit')
    status = False
    if request.method == 'POST' and form.validate():
        key_name, kwds = prepare(form)
        kwds['html'] = render_jinja('cache_body.html', body=kwds['body'])
        if post.key().name() == key_name:
            post = update_entity(key_name, **kwds)
            status = 'Updated'
        else:
            kwds['author'] = users.get_current_user()
            created, entity = create_entity(key_name, **kwds)
            if not created:
                return Response('sorry, post with that pub_date and title'\
                                    + 'exists already')
            post.delete()
            post = entity
            status = 'Updated'
            if form.save.data:
                return redirect('/admin/articles/', 301)
    return render_template('articles/form.html', form=form, post=post, status=status)

def delete(request, key):
    post = Post.get_by_key_name(key)
    if request.method == 'POST':
        post.delete()
        return redirect('/admin/', 301)
    return render_template('post_confirm_delete.html', post=post)


################################################################################
# The Wiki Engine
################################################################################

