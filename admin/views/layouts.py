# -*- coding: utf-8 -*-
from google.appengine.api import users
from datetime import datetime
from werkzeug import redirect
from utils import render_template
from models.pages import Layout
from admin.forms import LayoutForm, ConfirmDeleteLayoutForm
# in case we need the list function
_list = list

################################################################################
# Helper
################################################################################

################################################################################
# Views
################################################################################
def list(request):
    layouts = Layout.all().order('name')
    return render_template('layouts/list.html', layouts=layouts)

def add(request):
    form = LayoutForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        body = form.body.data
        layout = Layout(name=name, body=body,
                        author=users.get_current_user(),
                        updated=datetime.now())
        layout.put()
        if form.save.data is True:
            return redirect('/admin/layouts/', 301)
        if form.cont.data is True:
            return redirect('/admin/layouts/edit/%s/' % layout.key(), 301)
    return render_template('layouts/form.html', form=form)

def edit(request, key):
    layout = Layout.get(key)
    form = LayoutForm(request.form, obj=layout)
    if request.method == "POST" and form.validate():
        form.auto_populate(layout)
        layout.put()
        # clear depending caches
        for node in layout.get_affected_nodes():
            node.invalidate_cache()
        if form.save.data is True:
            return redirect('/admin/layouts/', 301)
    return render_template('layouts/form.html', form=form, layout=layout)

def delete(request, key):
    layout = Layout.get(key)
    form = ConfirmDeleteLayoutForm(request.form)
    if request.method == "POST" and form.validate():
        if form.drop.data is True:
            layout.delete()
            return redirect('/admin/layouts/', 301)
    return render_template('layouts/confirm_delete.html', layout=layout, form=form)
