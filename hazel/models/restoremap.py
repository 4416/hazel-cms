# -*- coding: utf-8 -*-

from google.appengine.ext import db
class RestoreMap(db.Model):
    @classmethod
    def create_or_update(cls, key, sink):
        def txn(key, sink=sink):
            node = cls.get_by_key_name('source:%s' % key)
            if not node:
                node = cls(key_name='source:%s' % key, sink=sink)
            else:
                node.sink = sink
            node.put()
            return node
        return db.run_in_transaction(txn, key, sink=sink)
    @classmethod
    def sink_for_key(cls, key):
        node = cls.get_by_key_name('source:%s' % key)
        if node:
            node = node.sink
        return node
    sink   = db.StringProperty(u'sink', required=True)
