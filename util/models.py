# -*- coding: utf-8 -*-
################################################################################
# A Sorted Materialized Path Model for GAE
################################################################################
# Author: Moritz Angermann
# Date: 22-01-2009


class MissingException(Exception):
	pass

class BadArgumentException(Exception):
	pass

from google.appengine.ext import db
from logging import info
from util.tools import debug_node, debug_nodes
from types import StringTypes
PREPEND = 0
APPEND  = 1
SUBTREE = 2

sep = u'.'

def update_full(key, nodes):
	nodes[key].path = u'%s%s%s' % (nodes[nodes[key].ancestors[-1]].path,
								   sep, nodes[key].pos)
	if len(nodes[key].children) < 1:
		return nodes
	keys = [k for k in nodes[key].children if k not in nodes.keys()]
	for node in db.get(keys):
		nodes[node.get_key()] = node
	for child in nodes[key].children:
		nodes[child].ancestors = nodes[key].ancestors + [key]
		nodes[child].path = u'%s%s%s' % (nodes[key].path, sep,
										 nodes[child].pos)
		nodes = update_full(child, nodes)
	return nodes

def update_path(key, nodes):
	info("calling update_path on %s" % nodes[key])
	nodes[key].path = u'%s%s%s' % (nodes[nodes[key].ancestors[-1]].path,
								   sep, nodes[key].pos)
	if len(nodes[key].children) < 1:
		return nodes
	keys = [k for k in nodes[key].children if k not in nodes.keys()]
	for node in db.get(keys):
		nodes[node.get_key()] = node
	for child in nodes[key].children:
		nodes[child].path = u'%s%s%s' % (nodes[key].path, sep,
										 nodes[child].pos)
		nodes = update_path(child, nodes)
	return nodes

def single_kw_deco(kwds):
	def __fn(fn):
		def _fn(*args, **kwargs):
			if len([1 for x in kwargs.keys() if x in kwds]) > 1:
				raise BadArgumentException("only one of " \
										   + '", "'.join(kwds) \
										   + " allowed, got: " \
										   + '", "'.join(u'%s:%s' % item \
														 for item in kwargs.items()))
			return fn(*args, **kwargs)
		return _fn
	return __fn

def min_one_kw(fn):
	def _fn(*args, **kwargs):
		if len(kwargs.keys()) < 1:
			raise BadArgumentException("at least one kw argument is required")
		return fn(*args, **kwargs)
	return _fn


# FIXME! Obviously this is stupid!
def ensure_stripped_strings(fn):
	def clean(arg):
		if type(arg) in StringTypes:
			return arg.strip()
		return arg
	def _fn(*args, **kwargs):
		return fn(*(args and (clean(arg) for arg in args) or []),
				  **(kwargs and dict(((k,clean(v)) for k,v in kwargs.iteritems())) or {}))
	return _fn

class SortedMPNode(db.Model):
	# properties
	path     = db.StringProperty(default='0')
	pos      = db.IntegerProperty(default=0)

	# transaction limitations
	ancestors = db.StringListProperty()
	siblings  = db.StringListProperty()
	children  = db.StringListProperty()

	def get_key(self):
		return u"%s" % self.key()

	@classmethod
	@ensure_stripped_strings
	@single_kw_deco(['to','before','after'])
	def add(cls, to=None, before=None, after=None, **kwds):
		if to is not None:
			return cls.insert(parent=to, **kwds)
		if before is not None:
			return cls.insert(before=before, **kwds)
		if after is not None:
			return cls.insert(after=after, **kwds)
		return cls.insert(**kwds)

	@classmethod
	@ensure_stripped_strings
	@single_kw_deco(['to','before','after'])
	@min_one_kw
	def move(cls, key, to=None, before=None, after=None):
		if to is not None:
			return cls.relocate(key, relative_to=to, mode=SUBTREE)
		if before is not None:
			return cls.relocate(key, relative_to=before, mode=PREPEND)
		if after is not None:
			return cls.relocate(key, relative_to=after, mode=APPEND)
		raise BadArgumentException('invalid args')

	@classmethod
	@ensure_stripped_strings
	def drop(cls, key, cascade=False):
		return cls.remove(key, all=cascade)

	@classmethod
	def root(cls):
		return cls.get_or_insert('root')

	@classmethod
	@ensure_stripped_strings
	def insert(cls, parent=None, before=None, **kwds):
		"""Insert a node with ``name'' to
		   as a child of ``parent'' before
		   the sibling ``before''"""

		def txn(node_key, parent_key, before=None, after=None):
			sep = u'.'
			parent, node = db.get([parent_key, node_key])
			if before is not None:
				if before not in parent.children:
					raise MissingException(u'"%s" not child of "%s"' \
										   % (before, parent.get_key()))
				children = db.get(parent.children)
				inc = False
				parent.children = []
				for child in children:
					child.siblings += [node.get_key()]
					if str(child.key()) == before:
						node.pos = child.pos
						inc = True
						parent.children += [node.get_key()]
					if inc:
						child.pos += 1
						child.path = sep.join([child.path.rsplit(sep,1)[0],
											   str(child.pos)])
					parent.children += [child.get_key()]
			elif after is not None:
				if after not in parent.children:
					raise MissingException(u'"%s" not child of "%s"' \
										   % (before, parent.get_key()))
				children = db.get(parent.children)
				inc = False
				parent.children = []
				for child in children:
					child.siblings += [node.get_key()]
					if inc:
						child.pos += 1
						child.path = sep.join([child.path.rsplit(sep,1)[0],
											   str(child.pos)])
					parent.children += [child.get_key()]
					if str(child.key()) == after:
						node.pos = child.pos
						inc = True
						parent.children += [node.get_key()]
			else:
				children = db.get(parent.children)
				for child in children:
					child.siblings += [node.get_key()]
				node.pos = len(children)
				parent.children += [node.get_key()]
			node.siblings = [child.get_key() for child in children]
			node.path = sep.join([parent.path, str(node.pos)])
			db.put([parent, node] + children)
			return True

		root = cls.root()
		if parent is not None:
			parent = cls.get(parent)
		else:
			parent = root
		# assume failed transaction
		tx = None
		node = None
		try:
			node = cls(parent=root,
					   ancestors=parent.ancestors+[parent.get_key()],
					   **kwds)
			node.put() 
			tx = db.run_in_transaction(txn, node.key(), parent.key(), before)
		finally:
			if tx is None and node is not None:
				node.delete()
		return node

	@classmethod
	def relocate(cls, node_key, relative_to, mode=PREPEND):

		def prepend_txn(node_key, relative_to):
			""" moves a node infront of the given relative node """
			node, target = db.get([node_key, relative_to])
			if node.ancestors[-1] == target.ancestors[-1]:
				# this basically means we don't have to care
				# about the ancestors tree. we only have
				# the siblings to follow the right order
				# as well as update our parents children.
				# finally we should update the path
				parent = node.ancestors[-1]
				siblings = node.siblings

				keys = list(set([parent]+siblings))
				if node_key in keys:
					# should be in there!
					# because ``relative_to`` is a sibling of ``node_key``
					keys.remove(relative_to)
				nodes = dict([(n.get_key(),n) for n in db.get(keys)])
				nodes[node_key] = node
				nodes[relative_to] = target

				np = nodes[node_key].pos

				# detach
				for sibling in siblings:
					if nodes[sibling].pos >= np:
						nodes[sibling].pos -= 1
					update_path(sibling, nodes)
				
				# reattach
				rp = nodes[relative_to].pos
				nodes[node_key].pos = rp
				for sibling in siblings:
					if nodes[sibling].pos >= rp:
						nodes[sibling].pos += 1
					update_path(sibling, nodes)

				nodes = update_path(node_key, nodes)
				db.put(nodes.values())
				return True
			else:
				old_parent, new_parent = node.ancestors[-1], target.ancestors[-1]
				old_siblings, new_siblings = node.siblings, target.siblings

				keys = [old_parent, new_parent] + old_siblings + new_siblings
				keys = list(set(keys))
				if node_key in keys:
					keys.remove(node_key)
				if relative_to in keys:
					keys.remove(relative_to)
				nodes = dict([(n.get_key(),n) for n in db.get(keys)])
				nodes[node_key] = node
				nodes[relative_to] = target
				
				# detache (remove from parent and siblings)
				nodes[old_parent].children.remove(node_key)
				for sibling in old_siblings:
					nodes[sibling].siblings.remove(node_key)
					if nodes[sibling].pos >= node.pos:
						nodes[sibling].pos -= 1
						nodes = update_path(sibling, nodes)

				# attach
				nodes[node_key].ancestors = nodes[relative_to].ancestors
				nodes[node_key].pos = nodes[relative_to].pos
				nodes[node_key].siblings = [relative_to]
				nodes[relative_to].siblings.append(node_key)

				nodes = update_full(node_key, nodes)
				nodes[new_parent].children = []
				nodes[relative_to].pos += 1
				rp = nodes[relative_to].pos - 1
				# using a dict to sort the nodes
				lookup = dict()
				for sibling in new_siblings:
					if sibling == node_key:
						continue
					nodes[sibling].siblings.append(node_key)
					nodes[node_key].siblings.append(sibling)
					if nodes[sibling].pos > rp:
						nodes[sibling].pos += 1
						nodes = update_path(sibling, nodes)
					lookup[nodes[sibling].pos] = sibling
									
				lookup[rp] = node_key
				lookup[rp+1] = relative_to

				# automatically sorted, because it's a list!
				nodes[new_parent].children = lookup.values()
				nodes = update_path(relative_to, nodes)
				db.put(nodes.values())
				return True

		def append_txn(node_key, relative_to):
			""" moves a node after the given relative node """
			node, target = db.get([node_key, relative_to])
			if node.ancestors[-1] == target.ancestors[-1]:
				# this basically means we don't have to care
				# about the ancestors tree. we only have
				# the siblings to follow the right order
				# as well as update our parents children.
				# finally we should update the path
				parent = node.ancestors[-1]
				siblings = node.siblings

				keys = list(set([parent]+siblings))
				if node_key in keys:
					# should be in there!
					# because ``relative_to`` is a sibling of ``node_key``
					keys.remove(relative_to)
				nodes = dict([(n.get_key(),n) for n in db.get(keys)])
				nodes[node_key] = node
				nodes[relative_to] = target

				np = nodes[node_key].pos
				
				# detach
				for sibling in siblings:
					if nodes[sibling].pos >= np:
						nodes[sibling].pos -= 1
					update_path(sibling, nodes)

				# reattach
				rp = nodes[relative_to].pos
				nodes[node_key].pos = rp + 1
				
				for sibling in siblings:
					if nodes[sibling].pos > rp:
						nodes[sibling].pos += 1
					update_path(sibling, nodes)

				nodes = update_path(node_key, nodes)
				
				db.put(nodes.values())
				return True
			else:
				old_parent, new_parent = node.ancestors[-1], target.ancestors[-1]
				old_siblings, new_siblings = node.siblings, target.siblings

				keys = [old_parent, new_parent] + old_siblings + new_siblings
				keys = list(set(keys))
				if node_key in keys:
					keys.remove(node_key)
				if relative_to in keys:
					keys.remove(relative_to)
				nodes = dict([(n.get_key(),n) for n in db.get(keys)])
				nodes[node_key] = node
				nodes[relative_to] = target
				
				# detache (remove from parent and siblings)
				nodes[old_parent].children.remove(node_key)
				for sibling in old_siblings:
					nodes[sibling].siblings.remove(node_key)
					if nodes[sibling].pos >= node.pos:
						nodes[sibling].pos -= 1
						nodes = update_path(sibling, nodes)

				# attach
				nodes[node_key].ancestors = nodes[relative_to].ancestors
				nodes[node_key].pos = nodes[relative_to].pos + 1
				nodes[node_key].siblings = [relative_to]
				nodes[relative_to].siblings.append(node_key)

				nodes = update_full(node_key, nodes)
				nodes[new_parent].children = []
				rp = nodes[relative_to].pos
				# using a dict to sort the nodes
				lookup = dict()
				for sibling in new_siblings:
					if sibling == node_key:
						continue
					nodes[sibling].siblings.append(node_key)
					nodes[node_key].siblings.append(sibling)
					if nodes[sibling].pos > rp:
						nodes[sibling].pos += 1
						nodes = update_path(sibling, nodes)
					lookup[nodes[sibling].pos] = sibling
									
				lookup[rp] = node_key
				lookup[rp+1] = relative_to

				# automatically sorted, because it's a list!
				nodes[new_parent].children = lookup.values() 
				nodes = update_path(relative_to, nodes)
				db.put(nodes.values())
				return True

		def subtree_txn(node_key, relative_to):
			""" make node_key a child of relative_to (appended)
			    1. detach node (remove from parent and siblings)
				2. add node as child of relative_to
				3. add node as sibling of relative_to children
				4. set node.position to be the last of relative_to
				affected nodes: node, target, target.children
				node.fulltree
			"""
			node, target = db.get([node_key, relative_to])
			if node_key in target.children:
				# nothing to do
				return False
			parent = node.ancestors[-1]
			keys = [parent] + node.siblings + target.children
			keys = list(set(keys))
			if node_key in keys:
				keys.remove(node_key)
			if relative_to in keys:
				keys.remove(relative_to)
			nodes = dict([(n.get_key(),n) for n in db.get(keys)])
			nodes[node_key] = node
			nodes[relative_to] = target
			
			# detach
			nodes[parent].children.remove(node_key)
			for sibling in nodes[node_key].siblings:
				nodes[sibling].siblings.remove(node_key)
				if nodes[sibling].pos > nodes[node_key].pos:
					nodes[sibling].pos -= 1
					nodes = update_path(sibling, nodes)
			# attach
			nodes[node_key].ancestors = nodes[relative_to].ancestors + [relative_to]
			nodes[node_key].pos = len(nodes[relative_to].children)
			nodes[node_key].siblings = list(nodes[relative_to].children)
			for child in nodes[relative_to].children:
				nodes[child].siblings.append(node_key)
			nodes[relative_to].children.append(node_key)
			nodes = update_full(node_key, nodes)
			db.put(nodes.values())
			return True
		
		fn = {PREPEND: prepend_txn,
			  APPEND:  append_txn,
			  SUBTREE: subtree_txn}
		# assume failed transaction
		tx = db.run_in_transaction(fn[mode], node_key, relative_to)

	@classmethod
	def remove(cls, node_key, all=False):
		def txn(node_key, all=False):
			if all:
				def get_children(node):
					children = db.get(node.children)
					nodes = list(children)
					for child in children:
						nodes += get_children(child)
					return nodes
				node = db.get(node_key)
				parent = node.ancestors[-1]
				remove = [node]
				remove += get_children(node)
				nodes = dict([(n.get_key(), n) for n in db.get([parent] \
															   + node.siblings)])
				nodes[parent].children.remove(node_key)
				for sibling in node.siblings:
					nodes[sibling].siblings.remove(node_key)
					if nodes[sibling].pos > node.pos:
						nodes[sibling].pos -= 1
						nodes = update_path(sibling, nodes)
				db.put(nodes.values())
				db.delete(remove)
			else:
				node = db.get(node_key)
				parent = node.ancestors[-1]
				children = node.children
				nodes = dict([(n.get_key(), n) for n in db.get([parent] \
															   + node.siblings \
															   + children)])
				# update children
				N = len(children)
				for child in children:
					nodes[child].ancestors = node.ancestors
					nodes[child].pos += node.pos
					nodes[child].siblings += node.siblings
					nodes = update_full(child, nodes)
				
				for sibling in node.siblings:
					if nodes[sibling].pos > node.pos:
						nodes[sibling].pos += N-1
						nodes = update_path(sibling, nodes)
					nodes[sibling].siblings.remove(node_key)
					nodes[sibling].siblings += node.children
					
				nodes[parent].children = nodes[parent].children[:node.pos] \
										 + node.children \
										 + nodes[parent].children[node.pos+1:]
				db.put(nodes.values())
				db.delete(node)

		tx = db.run_in_transaction(txn, node_key, all)
		
	def __unicode__(self):
		return u'<%s: %s %s>' % (self.__class__.__name__, self.path, self.name)
	
	def __str__(self):
		return '<%s: %s %s>' % (self.__class__.__name__, self.path, self.name)

	def __repr__(self):
		return str(self)

class Menu(SortedMPNode):
	name     = db.StringProperty(default='root')
