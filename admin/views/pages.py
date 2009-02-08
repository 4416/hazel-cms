# -*- coding: utf-8 -*-
from models.pages import Node, FOLDER, PAGE, Layout, Block
from admin.forms import FolderForm, PageForm, ConfirmDeleteForm, BlockAddForm, BlockForm
from util.tools import sort_nicely, slugify, rec
from utils import render_template, pager
from logging import info
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import datetime
from werkzeug import redirect

import wtforms

fn = wtforms.fields.SelectField._selected
def _fn(s,v):
    info("- %s" % v)
    try:
        info("= %s" % s.data.key())
    except:
        info("= %s" % s.data)
    info("> %s" % s.coerce(v))
    res = fn(s,v)
    info("=> %s" % res)
    return res
wtforms.fields.SelectField._selected = _fn

################################################################################
# Views
################################################################################
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

def add(request, to=None):
    """ add a new page
        to the set"""
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
                return redirect('/admin/pages/', 301)
            if form.cont.data is True:
                return redirect('/admin/pages/edit/%s' % page.get_key(), 301)
        info(form.errors)
        for name, block in blocks:
            info(name)
            info(block.errors)

    return render_template('pages/form.html', form=form, add=add, blocks=blocks)

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
                info(form.layout.data)
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
                return redirect('/admin/pages/', 301)
            if layout_val is not None:
                form.layout.data = layout_val
    return render_template('pages/form.html', form=form, add=add, blocks=blocks.items(), mode='edit', node=node)

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
            return redirect('/admin/pages/', 301)

    node = Node.get(key)
    nodes = dict([(n.get_key(), n) for n in Node.all().filter("ancestors = ", key)])
    node = rec(node, nodes)
    return render_template('pages/confirm_delete.html', form=form,
                           node=node)

def add_folder(request):
    form = FolderForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        slug = form.slug.data
        breadcrumb = form.breadcrumb.data
        state = form.state.data
        active = form.active.data
        info(slug)
        if len(slug) < 1:
            slug = slugify(name)
        author = users.get_current_user()
        updated = datetime.now()

        page = Node.add(name=name, slug=slug, breadcrumb=breadcrumb,
                         updated=updated, author=author,
                         state=state, active=active, type=FOLDER)
        if form.save.data is True:
            return redirect('/admin/pages/', 301)
        if form.cont.data is True:
            return redirect('/admin/pages/edit/%s' % page.get_key(), 301)
    return render_template('pages/form.html', form=form)

def move(request, A, mode, B):
    info("'%s'-%s-'%s'" % (A, mode, B))
    switch = { 'before': lambda x,y: Node.move(x, before=y),
               'after': lambda x,y: Node.move(x, after=y),
               'to': lambda x,y: Node.move(x, to=y) }
    switch[mode](A,B)
    info("Done")
    return redirect('/admin/pages/', 301)


def migrate(request):
    from models.pages import File
    
    for n in File.all():
        if len(n.ancestors) < 1:
            continue
        _slug = n.slug
        n.slug = _slug + u'-'
        n.update()
        n.slug = _slug
        n.update()

    from models.pages import Node

    for n in Node.all():
        if len(n.ancestors) < 1:
            continue
        _slug = n.slug
        n.slug = _slug + u'-'
        n.update()
        n.slug = _slug
        n.update()
    
    from models.pages import Layout

    for layout in Layout.all():
        layout.put()

    from utils import Response
    return Response("updated")
