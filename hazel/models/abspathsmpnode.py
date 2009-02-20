# -*- coding: utf-8 -*-
# global
# appengine
from google.appengine.ext import db
from google.appengine.api import memcache
# libs

# local
from hazel.models import SortedMPNode

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

    def get_absolute_url(self, **kwargs):
        from hazel.util.globals import url_for
        return url_for(self._endpoint, key=self.abs_path, **kwargs)

