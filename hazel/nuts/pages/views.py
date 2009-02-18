# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import memcache

from werkzeug import redirect
import wtforms

from hazel.admin.forms import FolderForm, PageForm, ConfirmDeleteForm, BlockAddForm, BlockForm
from hazel.admin.forms import LayoutForm, ConfirmDeleteLayoutForm


from hazel.util.decorators import memcached
from hazel.util.globals import url_for
from hazel.util.helper import render_template
from hazel.util.helper import layout_response_from_string
from hazel.util.tools import sort_nicely
from hazel.util.tools import slugify
from hazel.util.tools import rec
from hazel.util.tools import pager
from hazel.util.net import Response

from urls import expose, expose_admin

from models import PAGE
from models import FOLDER
from models import Node
from models import Layout
from models import Block

################################################################################
# Public Views
@expose('/', defaults={'key': ''})
@expose('/<path:key>')
@memcached
def show(request, key):
    # eventually the key should be the "abs_path"
    page = Node.all().filter('type =', PAGE).filter('abs_path = ', key).get()
    if page is None:
        raise Exception("Page not found")
    if page.layout is None:
        raise Exception("invalid layout")
    string = [
            "{%% extends '%s' %%}" % page.layout.name,
            "{%% block body %%} %s {%% endblock %%}" % page.body ]
    for block in page.blocks:
        string.append("{%% block %s %%} %s {%% endblock %%}" % (block.name, block.body))
    resp = layout_response_from_string('\n'.join(string), page.content_type, title=page.name)
    resp.expires = datetime.now() + timedelta(7)
    return resp

################################################################################
# Admin Views
@expose_admin('/p/', tab='Pages')
def list_pages(request):
    nodes = dict([(n.get_key(), n) for n in Node.all()])
    root = None
    for node in nodes:
        node = nodes[node]
        if node.path == '0':
            root = node
            break
    if root is not None:
        root = rec(root, nodes)
    return render_template('pages/list.html', root=root)

@expose_admin('/p/add/', defaults={'key': None})
@expose_admin('/p/add/<key>/')
def add(request, key):
    """ add a new page
        to the set"""
    to = key # lame but it does the trick for now
    blocks = []
    form = PageForm(request.form)
    add  = BlockAddForm(request.form, prefix='_add')
    form.layout.choices = [('Layout:None', '---')] + [(unicode(l), l.name) for l in Layout.all().order('name')]
    if request.method == 'POST':
        # some logic to find __block elements.
        for key in request.form:
            if key.startswith('__block:'):
                name = key.split('__',2)[1][6:]
                blocks.append((name, BlockForm(request.form, prefix='__block:%s__' % name)))
        if add.validate() and add.add.data is True:
            blocks.append((add.name.data, BlockForm(prefix='__block:%s__' % add.name.data)))
            add = BlockAddForm(prefix='_add')
        elif form.validate() and all([block.validate() for _, block in blocks]):
            name = form.name.data
            slug = form.slug.data
            breadcrumb = form.breadcrumb.data
            state = form.state.data
            active = form.active.data
            if len(slug) < 1:
                slug = slugify(name)
            author = users.get_current_user()
            updated = datetime.now()

            description = form.description.data
            keywords = form.keywords.data
            body = form.body.data
            content_type = form.content_type.data
            if form.layout.data == 'Layout:None':
                layout = None
            else:
                layout = Layout.get(form.layout.data.split(':',1)[1])
            page = Node.add(to=to, name=name, slug=slug, breadcrumb=breadcrumb,
                            updated=updated, author=author, body=body,
                            description=description, keywords=keywords, layout=layout,
                            content_type=content_type,
                            state=state, active=active, type=PAGE)
            done = []
            try:
                for name, block in blocks:
                    b = Block(node=page, name=name, body=block.body.data)
                    b.put()
                    done.append(b)
            except:
                db.delete(done)
                Node.drop(page.get_key())
            if form.save.data is True:
                return redirect(url_for('nut:pages/list_pages'), 301)
            if form.cont.data is True:
                return redirect(url_for('nut:pages/edit', key=page.get_key()), 301)

    return render_template('pages/form.html', form=form, add=add, blocks=blocks)

@expose_admin('/p/edit/<key>/')
def edit(request, key):
    blocks = {}
    node = Node.get(key)
    add  = BlockAddForm(request.form, prefix='_add')
    if node.type == FOLDER:
        form = FolderForm(request.form, obj=node)
    else:
        form = PageForm(request.form, obj=node)
        form.layout.choices = [('Layout:None', '---')] + [(unicode(l), l.name) for l in Layout.all().order('name')]
        for block in node.blocks:
            blocks[block.name] = BlockForm(request.form, obj=block, prefix='__block:%s__' % block.name)

    if request.method == 'POST':
        blocks = dict(blocks)
        for key in request.form:
            if key.startswith('__block:'):
                name = key.split('__',2)[1][6:]
                if name not in blocks:
                    blocks[name] = BlockForm(request.form, prefix='__block:%s__' % name)
        if add.validate() and add.add.data is True:
            blocks[add.name.data] = BlockForm(prefix='__block:%s__' % add.name.data)
            add = BlockAddForm(prefix='_add')
        elif form.validate() and all([blocks[block].validate() for block in blocks]):
            layout_val = None
            if node.type == PAGE:
                layout_val = form.layout.data
                keys = blocks.keys()
                if form.layout.data == 'Layout:None':
                    form.layout.data = None
                else:
                    form.layout.data = Layout.get(form.layout.data.split(':',1)[1])
                for block in node.blocks:
                    blocks[block.name].auto_populate(block)
                    keys.remove(block.name)
                    block.put()
                for block in keys:
                    block = Block(node=node, name=block, body=blocks[block].body.data)
                    block.put()
            form.auto_populate(node)
            node.update()
            # invalidate cache
            node.invalidate_cache()

            if form.save.data is True:
                return redirect(url_for('nut:pages/list_pages'), 301)
            if layout_val is not None:
                form.layout.data = layout_val
    return render_template('pages/form.html', form=form, add=add, blocks=blocks.items(), mode='edit', node=node)

@expose_admin('/p/delete/<key>/')
def delete(request, key):
    form = ConfirmDeleteForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.drop.data is True:
            node = Node.get(key)
            db.delete(node.blocks)
            Node.drop(key)
            return redirect('/admin/pages/', 301)
        if form.cascade.data is True:
            # cascade callback
            # inject a cascade callback that does
            #            # try to delete the key
            #            for i in range(2):
            #                if memcache.delete(node.get_absolute_url()) > 0:
            #                    break
            Node.drop(key, cascade=True)
            # FIXME: remove blocks from dropped Nodes
            return redirect(url_for('nut:pages/list_pages'), 301)

    node = Node.get(key)
    nodes = dict([(n.get_key(), n) for n in Node.all().filter("ancestors = ", key)])
    node = rec(node, nodes)
    return render_template('pages/confirm_delete.html', form=form,
                           node=node)

@expose_admin('/p/add_folder/')
def add_folder(request):
    form = FolderForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        slug = form.slug.data
        breadcrumb = form.breadcrumb.data
        state = form.state.data
        active = form.active.data
        if len(slug) < 1:
            slug = slugify(name)
        author = users.get_current_user()
        updated = datetime.now()

        page = Node.add(name=name, slug=slug, breadcrumb=breadcrumb,
                         updated=updated, author=author,
                         state=state, active=active, type=FOLDER)
        if form.save.data is True:
            return redirect(url_for('nut:pages/list_pages'), 301)
        if form.cont.data is True:
            return redirect(url_for('nut:pages/edit', key=page.get_key()), 301)
    return render_template('pages/form.html', form=form)

@expose_admin('/p/move/<A>/<mode>/<B>/')
def move(request, A, mode, B):
    switch = { 'before': lambda x,y: Node.move(x, before=y),
               'after': lambda x,y: Node.move(x, after=y),
               'to': lambda x,y: Node.move(x, to=y) }
    switch[mode](A,B)
    return redirect(url_for('nut:pages/list_pages'), 301)

################################################################################
# Layout
################################################################################

################################################################################
# pub Views

@expose_admin('/l/', tab='Layouts')
def list_layous(request):
    layouts = Layout.all().order('name')
    return render_template('layouts/list.html', layouts=layouts)

@expose_admin('/l/add/')
def add_layout(request):
    form = LayoutForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        body = form.body.data
        layout = Layout(name=name, body=body,
                        author=users.get_current_user(),
                        updated=datetime.now())
        layout.put()
        if form.save.data is True:
            return redirect(url_for('nut:pages/list_layouts'), 301)
        if form.cont.data is True:
            return redirect(url_for('nut:pages/edit', key=layout.key()), 301)
    return render_template('layouts/form.html', form=form)

@expose_admin('/l/edit/<key>/')
def edit_layout(request, key):
    layout = Layout.get(key)
    form = LayoutForm(request.form, obj=layout)
    if request.method == "POST" and form.validate():
        form.auto_populate(layout)
        layout.put()
        # clear depending caches
        for node in layout.get_affected_nodes():
            node.invalidate_cache()
        if form.save.data is True:
            return redirect(url_for('nut:pages/list_layouts'), 301)
    return render_template('layouts/form.html', form=form, layout=layout)

@expose_admin('/l/delete/<key>/')
def delete_layout(request, key):
    layout = Layout.get(key)
    form = ConfirmDeleteLayoutForm(request.form)
    if request.method == "POST" and form.validate():
        if form.drop.data is True:
            layout.delete()
            return redirect(url_for('nut:pages/list_layouts'), 301)
    return render_template('layouts/confirm_delete.html', layout=layout, form=form)
