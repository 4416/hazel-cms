# -*- coding: utf-8 -*-
from logging import info
from datetime import datetime
from datetime import timedelta

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

from werkzeug import redirect

from util.helper import render_template
from util.net import Response
from util.decorators import memcached
from util.constants import file_ext_to_content_type
from util.tools import slugify, rec
from models.pages import File, FOLDER, FILE, Node
from admin.forms import FolderForm, FileForm, FileEditForm, FileConfirmDeleteForm
# in case we need the list function
_list = list


################################################################################
# Views
################################################################################
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

def add(request, to=None, type=FILE):
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
            return redirect('/admin/files/', 301)
        if form.cont.data is True:
            return redirect('/admin/files/edit/%s/' % file.key(), 301)
    return render_template('files/form.html', form=form)

def edit(request, key):
    file = File.get(key)
    form = FileEditForm(request.form, obj=file)
    if request.method == "POST" and form.validate():
        form.auto_populate(file)
        file.put()
        if form.save.data is True:
            return redirect('/admin/files/', 301)
    return render_template('files/form.html', form=form, file=file)

def delete(request, key):
    form = FileConfirmDeleteForm(request.form)
    if request.method == "POST" and form.validate():
        if form.drop.data is True:
            File.drop(key)
            return redirect('/admin/files/', 301)
        if form.cascade.data is True:
            Node.drop(key, cascade=True)
            return redirect('/admin/pages/', 301)
    file = File.get(key)
    files = dict([(n.get_key(), n) for n in File.all().filter("ancestors = ", key)])
    file = rec(file, files)

    return render_template('files/confirm_delete.html', file=file, form=form)

def move(request, A, mode, B):
    switch = { 'before': lambda x,y: File.move(x, before=y),
                       'after': lambda x,y: File.move(x, after=y),
                       'to': lambda x,y: File.move(x, to=y) }
    switch[mode](A,B)
    return redirect('/admin/files/', 301)

@memcached
def show(request, key, type):
    file = File.all().filter('abs_path = ', key)\
           .filter('content_type =', file_ext_to_content_type[type]).get()
    return Response(file.data, mimetype=file.content_type)
