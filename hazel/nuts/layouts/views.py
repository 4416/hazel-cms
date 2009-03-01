# -*- coding: utf-8 -*-
from google.appengine.api import users
from google.appengine.ext import db
from werkzeug import redirect


from hazel.util.helper import render_template
from hazel.util.globals import url_for
from hazel.util.tools import rec
from hazel.util.tools import slugify

from urls import expose
from urls import expose_admin

from models import Layout
from models import PAGE
from models import LAYOUT
from models import FOLDER

from forms import LayoutForm
from forms import FolderForm
from forms import DeleteForm


@expose_admin('/', tab='Layouts')
def list(request):
    nodes = dict([(n.get_key(), n) for n in Layout.all()])
    root = None
    for node in nodes:
        node = nodes[node]
        if node.path == '0':
            root = node
            break
    if root is not None:
        root = rec(root, nodes)
    return render_template('app:layouts/list.html', root=root)

@expose_admin('/add/', defaults={'key': None})
@expose_admin('/add/<key>/')
def add(request, key):
    form = LayoutForm(request.form)
    if request.method == 'POST' and form.validate():
        layout = Layout.add(to=key, type=LAYOUT,
                            name=form.name.data,
                            slug=slugify(form.name.data),
                            body=form.body.data,
                            author=users.get_current_user())
        layout.update_extends()
        layout.put()
        if form.save.data is True:
            return redirect(url_for('nut:layouts/list'), 301)
        if form.cont.data is True:
            return redirect(url_for('nut:layouts/edit', key=layout.get_key()), 301)
    return render_template('app:layouts/form.html', form=form)

@expose_admin('/add_folder/')
def add_folder(request):
    form = FolderForm(request.form)
    if request.method == 'POST' and form.validate():
        layout = Layout.add(name=form.name.data,
                            slug=slugify(form.name.data),
                            author=users.get_current_user(),
                            type=FOLDER)
        if form.save.data is True:
            return redirect(url_for('nut:layouts/list'), 301)
        if form.cont.data is True:
            return redirect(url_for('nut:layouts/edit', key=layout.get_key()), 301)
    return render_template('app:layouts/form.html', form=form)

@expose_admin('/edit/<path:key>/')
def edit(request, key):
    layout = Layout.get(db.Key(key))
    form = LayoutForm(request.form, obj=layout)
    if request.method == "POST" and form.validate():
        form.auto_populate(layout)
        layout.put()
        # clear depending caches
        for node in layout.get_affected_nodes():
            node.invalidate_cache()
        if form.save.data is True:
            return redirect(url_for('nut:layouts/list'), 301)
    return render_template('app:layouts/form.html', form=form, layout=layout)
    

@expose_admin('/delete/<key>/')
def delete(request, key):
    layout = Layout.get(db.Key(key))
    if request.method == 'POST':
        Layout.drop(key)
        return redirect(url_for('nut:layouts/list'), 301)
    return render_template('app:layouts/confirm_delete.html', layout=layout, form=DeleteForm())

@expose_admin('/move/<A>/<mode>/<B>/')
def move(request, A, mode, B):
    switch = { 'before': lambda x,y: Layout.move(x, before=y),
               'after': lambda x,y: Layout.move(x, after=y),
               'to': lambda x,y: Layout.move(x, to=y) }
    switch[mode](A,B)
    return redirect(url_for('nut:layouts/list'), 301)
