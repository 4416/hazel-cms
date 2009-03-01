# -*- coding: utf-8 -*-
import re

from google.appengine.ext import db

from hazel.util.globals import url_for
from hazel.util.tools import sort_nicely

from hazel.models import AbsPathSMPNode

FOLDER = 0
PAGE   = 1
FILE   = 2
LAYOUT = 3

class Layout(AbsPathSMPNode):
    _extend_re = re.compile(r'{%\s+extends\s+("|\')(?P<extends>[^\1]*?)\1\s+%}')

    type = db.IntegerProperty(default=FOLDER, required=True)

    name = db.StringProperty(required=True, default='root')

    body = db.TextProperty()

    author = db.UserProperty()
    updated = db.DateTimeProperty(auto_now=True)

    extends = db.StringListProperty(default=[])

    def __unicode__(self):
        return u'Layout:%s' % self.key()

    def get_key(self):
        return u'%s' % self.key()

    def update_extends(self):
        self.extends = [match.group(2) for match in self._extend_re.finditer(self.body)]

    def get_extending(self):
        return Layout.all().filter('extends = ', self.name)

    def get_affected_nodes(self):
        if not hasattr(self, 'node_set'):
            return []
        nodes = [n for n in self.node_set]
        for layout in self.get_extending():
            nodes.extend(layout.get_affected_nodes())
        return nodes   

    @classmethod
    def get_key_to_path(cls):
        # build layout
        _map = {}
        _list = {}
        _result = [('Layout:None', '---')]
        for l in cls.all():
            if l.path == '0':
                continue
            _map[l.get_key()] = l
            _list[l.path] = l
        keys = _list.keys()
        sort_nicely(keys)
        for k in keys:
            _result.append((unicode(_list[k]),
                            '/'.join(map(lambda key: _map[key].name,
                                         _list[k].ancestors[1:])
                                     +[_list[k].name])))
        return _result
