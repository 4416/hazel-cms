# -*- coding: utf-8 -*-
from werkzeug import redirect
from utils import render_to_response, expose

@expose('/')
def index(request):
    latest = Post.pub().order('-pub_date').get()
    if latest is not None:
        return redirect(latest.get_absolute_url())
    return render_template('show_post.html')
