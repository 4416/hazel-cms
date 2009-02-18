# -*- coding: utf-8 -*-
from logging import info
from datetime import datetime
from datetime import timedelta

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

from werkzeug import redirect

from hazel.util.helper import render_template
from hazel.util.net import Response
from hazel.util.decorators import memcached
from hazel.util.constants import file_ext_to_content_type
from hazel.util.tools import slugify, rec
from hazel.util.globals import url_for
from hazel.admin.forms import FolderForm, FileForm, FileEditForm, FileConfirmDeleteForm

from urls import expose, expose_admin

from models import File
from models import FOLDER
from models import FILE

# in case we need the list function
_list = list


################################################################################
# Public Views
@expose('/file/<path:key>.<type>')
@memcached
def show(request, key, type):
    file = File.all().filter('abs_path = ', key)\
           .filter('content_type =', file_ext_to_content_type[type]).get()
    return Response(file.data, mimetype=file.content_type)
################################################################################
# Admin Views
@expose_admin('/', tab='Files')
def list(request):
    files = dict([(f.get_key(), f) for f in File.all()])
    root = None
    for file in files:
        file = files[file]
        if file.path == '0':
            root = file
            break
    if root is not None:
        root = rec(root, files)
    return render_template('files/list.html', root=root)

@expose_admin('/add_folder/',   endpoint='add_folder', defaults={'type': FOLDER })
@expose_admin('/add_to/<key>/', endpoint='add_to')
@expose_admin('/add/')
def add(request, key=None, type=FILE):
    to = key # lame but it does the trick for now
    if type == FOLDER:
        form = FolderForm(request.form)
    else:
        form = FileForm(request.form)
    if request.method == "POST" and form.validate():
        if len(form.slug.data) < 1:
            form.slug.data = slugify(form.name.data)
        if type == FOLDER:
            file = File.add(to=to,type=type, name=form.name.data,
                                            slug=form.slug.data,
                                            breadcrumb=form.breadcrumb.data,
                                            state=form.state.data,
                                            active=form.active.data,
                                            author=users.get_current_user(),
                                            updated=datetime.now())
        elif type == FILE:
            file = request.files.get('file')
            data = db.Blob(file.read())
            file = File.add(to=to,type=type, name=form.name.data,
                                            slug=form.slug.data,
                                            breadcrumb=form.breadcrumb.data,
                                            state=form.state.data,
                                            active=form.active.data,
                                            author=users.get_current_user(),
                                            updated=datetime.now(),
                                            content_type=file.content_type,
                                            data=data, size=len(data))

        if form.save.data is True:
            return redirect(url_for('nut:files/list'), 301)
        if form.cont.data is True:
            return redirect(url_for('nut:files/edit', key=file.key()), 301)
    return render_template('files/form.html', form=form)

@expose_admin('/edit/<key>/')
def edit(request, key):
    file = File.get(key)
    form = FileEditForm(request.form, obj=file)
    if request.method == "POST" and form.validate():
        form.auto_populate(file)
        file.put()
        if form.save.data is True:
            return redirect(url_for('nut:files/list'), 301)
    return render_template('files/form.html', form=form, file=file)

@expose_admin('/delete/<key>/')
def delete(request, key):
    form = FileConfirmDeleteForm(request.form)
    if request.method == "POST" and form.validate():
        if form.drop.data is True:
            File.drop(key)
            return redirect(url_for('nut:files/list'), 301)
        if form.cascade.data is True:
            File.drop(key, cascade=True)
            return redirect(url_for('nut:files/list'), 301)
    file = File.get(key)
    files = dict([(n.get_key(), n) for n in File.all().filter("ancestors = ", key)])
    file = rec(file, files)

    return render_template('files/confirm_delete.html', file=file, form=form)

@expose_admin('/move/<A>/<mode>/<B>/')
def move(request, A, mode, B):
    switch = { 'before': lambda x,y: File.move(x, before=y),
                       'after': lambda x,y: File.move(x, after=y),
                       'to': lambda x,y: File.move(x, to=y) }
    switch[mode](A,B)
    return redirect(url_for('nut:files/list'), 301)
