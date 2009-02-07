# -*- coding: utf-8 -*-

import re
from logging import info

def sort_nicely( l ): 
  """ Sort the given list in the way that humans expect. 
  """ 
  convert = lambda text: int(text) if text.isdigit() else text 
  alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
  l.sort( key=alphanum_key ) 


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = re.sub('(?u)[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

def rec(node, nodes):
	""" creates a tree like datastructure from a SortedMPNode set """
	children = {}
	prev = None
	last_pos = None
	for child in node.children:
		if last_pos is not None:
			children[last_pos].next = child
		nodes[child].prev = prev
		if prev is None:
			prev = child
		children[nodes[child].pos] = nodes[child]
		last_pos = nodes[child].pos
		rec(nodes[child], nodes)
	node.child_nodes = children
	return node

def simple_rec(node, nodes):
  """ same as rec above, just no prev, nex linking """
  ret = {}
  for child in node.children:
    if not nodes.has_key(child):
      continue
    simple_rec(nodes[child], nodes)
    ret[nodes[child].pos] = nodes[child]
  node.child_nodes = ret.values()
  return node


def debug_node(node, prefix=''):
  info("%sNode: %s, Pos: %d, Path: %s" % (prefix, node.name, node.pos, node.path))

def debug_nodes(nodes, prefix=''):
  for node in nodes:
    debug_node(nodes[node], "%s%s " % (prefix, node))
