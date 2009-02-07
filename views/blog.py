# -*- coding: utf-8 -*-
from werkzeug import redirect
from models.blog import Post
from utils import render_template, pager, memcached
from google.appengine.api import users
from urllib2 import quote

def index(request):
    latest = Post.pub().get()
    if latest:
        return redirect(quote((u'/%s' % latest.lookup).encode('utf-8')), 301)
    return render_template('empty.html')

@memcached
def show(request, key):
    prevent_cache = False
    post = Post.get_by_key_name('Published:%s' % key)
    if not post and users.is_current_user_admin():
        # admin might also try to retrieve the post by it's key!
        post = Post.get_by_key_name(key)
        prevent_cache = True
    if post:
        resp = render_template('show_post.html', post=post)
        resp.prevent_cache = prevent_cache
    resp render_template('404.html', request=request)
    resp.prevent_cache = True
    return resp

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

def direct(request, template):
    return render_template(template)
