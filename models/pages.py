# -*- coding: utf-8 -*-
from util.models import SortedMPNode
from google.appengine.ext import db
from google.appengine.api import memcache
from logging import info
from util.globals import url_for
from util.constants import content_type_to_file_ext
import re

HIDDEN    = 0
DRAFT     = 1
PUBLISHED = 2

FOLDER = 0
PAGE   = 1
FILE   = 2

class MethodMixin(object):
    def get_state(self):
        if self.active:
            return {HIDDEN   : u'Hidden',
                    DRAFT    : u'Draft',
                    PUBLISHED: u'Published' }[self.state]
        else:
            return u'Disabled'

    def is_cached(self):
        return not memcache.get(self.get_absolute_url()) == None

    def invalidate_cache(self):
        for i in range(2):
            if memcache.delete(self.get_absolute_url()) > 0:
                break

class AbsPathSMPNode(SortedMPNode):
    @classmethod
    def callbacks(cls):
        sep = u'/'
        def update_abs_path(node, parent):
            node.abs_path = sep.join([parent.abs_path, node.slug])
            if node.abs_path.startswith(sep):
                node.abs_path = node.abs_path[1:]
            return node
        return { 'update_path': update_abs_path,
                 'pre_add': update_abs_path }

    def update(self, *args, **kwargs):
        """ make sure update path is updated accordingly """
        update_cb = self.callbacks()['update_path']
        def txn(_node):
            node = db.get(_node.key())
            nodes = {_node.get_key(): _node}
            def update_path(key):
                nodes[key] = update_cb(nodes[key], nodes[nodes[key].ancestors[-1]])
                # if children exist, they need to be updated
                if len(nodes[key].children) > 0:
                    # update our nodes with the children
                    nodes.update(dict(((n.get_key(), n) for n \
                                       in db.get(nodes[key].children))))
                    # iterate over all children
                    for child in nodes[key].children:
                        update_path(child)

            if node.slug != _node.slug:
                # if they don't match, inject the parent for path building.
                nodes[_node.ancestors[-1]] = db.get(_node.ancestors[-1])
                # update recursivly
                update_path(_node.get_key())
            # put all modified nodes back into the store
            db.put(nodes.values())
            return _node
        return db.run_in_transaction(txn, self)

    def get_absolute_url(self):
        return url_for(self._endpoint, key=self.abs_path)

class Layout(db.Model):
    _extend_re = re.compile(r'{%\s+extends\s+("|\')(?P<extends>[^\1]*?)\1\s+%}')

    name = db.StringProperty(required=True)
    body = db.TextProperty()

    author = db.UserProperty()
    updated = db.DateTimeProperty()

    active = db.BooleanProperty(default=True)

    extends = db.StringListProperty(default=[])

    def __unicode__(self):
        return u'Layout:%s' % self.key()

    def get_state(self):
        if self.active:
            return u'Enabled'
        else:
            return u'Disabled'

    def get_key(self):
        return u'%s' % self.key()

    def put(self, *args, **kwargs):
        self.extends = [match.group(2) for match in self._extend_re.finditer(self.body)]
        return super(Layout, self).put(*args, **kwargs)

    def get_extending(self):
        return Layout.all().filter('extends = ', self.name)

    def get_affected_nodes(self):
        nodes = [n for n in self.node_set]
        for layout in self.get_extending():
            nodes.extend(layout.get_affected_nodes())
        return nodes


class Node(AbsPathSMPNode, MethodMixin):

    _endpoint = 'pages/show'

    type = db.IntegerProperty(default=FOLDER, required=True)

    name = db.StringProperty(required=True, default='root')

    abs_path = db.StringProperty(default='')

    slug = db.StringProperty(default='')
    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()
    state = db.IntegerProperty(default=HIDDEN)
    active = db.BooleanProperty(default=False)

    description = db.StringProperty()
    keywords = db.StringProperty()
    body = db.TextProperty()

    layout = db.ReferenceProperty(Layout)
    content_type = db.StringProperty(required=True, default='text/html')

class Block(db.Model):
    node = db.ReferenceProperty(Node, collection_name='blocks')
    name = db.StringProperty(required=True)
    body = db.TextProperty()

class File(AbsPathSMPNode, MethodMixin):

    _endpoint = 'files/show'

    type = db.IntegerProperty(default=FOLDER, required=True)
    name = db.StringProperty(required=True, default='root')

    abs_path = db.StringProperty(default='')

    slug = db.StringProperty(default='')
    breadcrumb = db.StringProperty()
    updated = db.DateTimeProperty()
    author = db.UserProperty()

    state = db.IntegerProperty(default=HIDDEN)
    active = db.BooleanProperty(default=False)

    content_type = db.StringProperty()
    data = db.BlobProperty()
    size = db.IntegerProperty(default=0)

    def get_absolute_url(self):
        if self.abs_path is not None:
            return url_for(self._endpoint, key=self.abs_path,
                           type=content_type_to_file_ext[self.content_type])
        info(self)
        return ''
