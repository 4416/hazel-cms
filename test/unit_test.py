# -*- coding: utf-8 -*-
################################################################################
# A Sorted Materialized Path Model for GAE // Testcases
################################################################################
# Author: Moritz Angermann
# Date: 22-01-2009

import unittest
import logging
from google.appengine.ext import db
from util.sortedmpnode import Menu, PREPEND, APPEND, SUBTREE, SortedMPNode
from util.tools import sort_nicely
import re
from random import randint

from test_models import ABC
from models.pages import Node

def find_node(name, cls=Menu):
    return cls.all().filter('name =', name).get()

def find(name, cls=Menu):
    return find_node(name,cls).get_key()

def list():
    nodes = Menu.all()
    d = {}
    for node in nodes:
        d[node.path] = node
    keys = d.keys()
    sort_nicely( keys )
    for key in keys:
        print key + ' ' + d[key].name

def detail():
    t = '\n' + '-' * 30 + '\n'
    print t.join(["Name: %s\n Key: %s\nPath: %s\n Pos: %d\nSibs: %s\nClds: %s\nAncs: %s" \
          % (n.name, n.get_key(),
             n.path, n.pos,
             ', '.join([s.name for s in db.get(n.siblings)]),
             ', '.join([s.name for s in db.get(n.children)]),
             ', '.join([s.name for s in db.get(n.ancestors)]))
   for n in Menu.all()])

def debug_list(test='undef'):
    nodes = {}
    keys = []
    for node in Menu.all():
        nodes[node.path] = node
        nodes[node.get_key()] = node
        keys.append(node.path)

    sort_nicely(keys)
    for key in keys:
        logging.info(u'[%s] %-10s %5s (%-12s | %-20s)' % (test, key, nodes[key].name,
                     u', '.join([nodes[n].name for n in nodes[key].siblings]),
                     u' > '.join([nodes[n].name for n in nodes[key].ancestors])))

def debug_details(fn,name):
    n = find_node(name)
    logging.info("[%s] %6s: %s" % (fn, 'Name', n.name))
    logging.info("[%s] %6s: %s" % (fn, 'Key' , n.get_key()))
    logging.info("[%s] %6s: %s" % (fn, 'Path', n.path))
    logging.info("[%s] %6s: %s" % (fn, 'Pos' , n.pos))
    logging.info("[%s] %6s: %s" % (fn, 'Sibs', ', '.join([s.name for s in db.get(n.siblings)])))
    logging.info("[%s] %6s: %s" % (fn, 'Clds', ', '.join([s.name for s in db.get(n.children)])))
    logging.info("[%s] %6s: %s" % (fn, 'Ancs', ', '.join([s.name for s in db.get(n.ancestors)])))

def print_rec(tup, prefix=0):
    for k in tup:
        logging.info(u'%s%s' % (' ' * prefix, k[0]))
        if len(k) > 1:
            print_rec(k[1],prefix+1)

def insert(data, parent=None):
    for d in data:
        if len(d) > 1:
            node, tree = d
        else:
            node = d[0]
            tree = None
        Menu.insert(name=node, parent=parent)
        if tree:
            insert(tree, find(node))

def to_list(e):
    from types import ListType, TupleType
    if type(e) not in [ListType, TupleType]:
        return e
    ret = []
    for k in e:
        ret.append(to_list(k))
    return ret


class TreeTest(unittest.TestCase):
    tree = (('A',),('B',),('C',),('D',),('E',),('F',))
    subtree = (('a',),('b',),('c',),('d',),('e',),('f',))

    def assertEqualTree(self, tree, parent='0', ancestors=[u'root'], cls=Menu):
        pos = 0
        expected_sibs = [unicode(k[0]) for k in tree]
        for k in tree:
            node = find_node(k[0],cls)
            # path
            self.assertEqual(node.path,u'%s%s%s' % (parent, u'.', pos))
            # siblings
            node_sibs = [db.get(n).name for n in node.siblings]
            node_sibs.sort()
            expected_sibs.remove(k[0])
            expected_sibs.sort()
            self.assertEqual(expected_sibs, node_sibs)
            expected_sibs.append(k[0])
            # ancestors
            node_ancestors = [db.get(n).name for n in node.ancestors]
            self.assertEqual(ancestors, node_ancestors)
            if len(k) > 1:
                # children
                expected_children = [unicode(l[0]) for l in k[1]]
                expected_children.sort()
                node_children = [db.get(n).name for n in node.children]
                node_children.sort()
                self.assertEqual(expected_children, node_children)
                # recurse
                self.assertEqualTree(k[1], u'%s%s%s' % (parent, u'.', pos), ancestors+[node.name])
            pos += 1


class ModelPublicMethodsTest(TreeTest):
    def setUp(self):
        db.delete(Menu.all())
        insert(self.tree)

    def tearDown(self):
        pass

    def test_add(self):
        Menu.add(name='G')
        expected = (('A',),('B',),('C',),('D',),('E',),('F',),('G',))
        self.assertEqualTree(expected)

    def test_add_to(self):
        Menu.add(name='G', to=find('A'))
        expected = (('A',(('G',),)),('B',),('C',),('D',),('E',),('F',))
        self.assertEqualTree(expected)

    def test_add_before(self):
        Menu.add(name='G', before=find('A'))
        expected = ((x,) for x in 'G,A,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_add_after(self):
        Menu.add(name='G', after=find('A'))
        expected = ((x,) for x in 'A,G,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_to(self):
        Menu.move(find('C'), to=find('B'))
        expected = [[x,] for x in 'A,B,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == 'B':
                expected[i].append(['C',])
        self.assertEqualTree(expected)

    def test_move_before(self):
        Menu.move(find('C'), before=find('B'))
        expected = [[x,] for x in 'A,C,B,D,E,F'.split(',')]
        self.assertEqualTree(expected)

    def test_move_after(self):
        Menu.move(find('C'), after=find('D'))
        expected = [[x,] for x in 'A,B,D,C,E,F'.split(',')]
        self.assertEqualTree(expected)

    def test_drop(self):
        Menu.drop(find('C'))
        expected = [[x,] for x in 'A,B,D,E,F'.split(',')]
        debug_list('test_drop C post')
        self.assertEqualTree(expected)

    def test_drop_sub(self):
        insert(self.subtree, parent=find('C'))
        Menu.drop(find('c'))
        expected = [[x,] for x in 'A,B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == 'C':
                expected[i].append([[x,] for x in 'a,b,d,e,f'.split(',')])
        self.assertEqualTree(expected)

    def test_drop_noncascade(self):
        insert(self.subtree, parent=find('C'))
        Menu.drop(find('C'))
        expected = [[x,] for x in 'A,B,a,b,c,d,e,f,D,E,F'.split(',')]
        self.assertEqualTree(expected)

    def test_drop_cascade(self):
        insert(self.subtree, parent=find('C'))
        Menu.drop(find('C'), cascade=True)
        expected = [[x,] for x in 'A,B,D,E,F'.split(',')]
        self.assertEqualTree(expected)


class ModelTest(TreeTest):

    def setUp(self):
        db.delete(Menu.all())
        insert(self.tree)

    def tearDown(self):
        pass

    def test_insert_last(self):
        Menu.insert(name='G')
        expected = (('A',),('B',),('C',),('D',),('E',),('F',),('G',))
        self.assertEqualTree(expected)

    def test_insert_middle(self):
        Menu.insert(name='G', before=find('C'))
        expected = (('A',),('B',),('G',),('C',),('D',),('E',),('F',))
        self.assertEqualTree(expected)

    def test_insert_first(self):
        Menu.insert(name='G', before=find('A'))
        expected = (('G',),('A',),('B',),('C',),('D',),('E',),('F',))
        self.assertEqualTree(expected)

    def test_insert_sub(self):
        k = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        Menu.insert(name='G', parent=find(k))
        expected = [[x,] for x in 'A,B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == k:
                expected[i].append(['G',])
        self.assertEqualTree(expected)

    def test_move_first_prepend(self):
        Menu.relocate(find('B'), relative_to=find('A'))
        expected = ((x,) for x in 'B,A,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_first_append(self):
        Menu.relocate(find('B'), relative_to=find('A'), mode=APPEND)
        expected = ((x,) for x in 'A,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_middle_prepend(self):
        Menu.relocate(find('C'), relative_to=find('D'))
        expected = ((x,) for x in 'A,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_middle_append(self):
        Menu.relocate(find('C'), relative_to=find('D'), mode=APPEND)
        expected = ((x,) for x in 'A,B,D,C,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_last_prepend(self):
        Menu.relocate(find('E'), relative_to=find('F'))
        expected = ((x,) for x in 'A,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_move_last_append(self):
        Menu.relocate(find('E'), relative_to=find('F'), mode=APPEND)
        expected = ((x,) for x in 'A,B,C,D,F,E'.split(','))
        self.assertEqualTree(expected)


    def test_move_one_down_first_prepend(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('a'), relative_to=find('A'))
        expected = [[x,] for x in 'a,A,B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'b,c,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_down_first_append(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('a'), relative_to=find('A'), mode=APPEND)
        expected = [[x,] for x in 'A,a,B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'b,c,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_down_middle_prepend(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('c'), relative_to=find('D'))
        expected = [[x,] for x in 'A,B,C,c,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_down_middle_append(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('c'), relative_to=find('C'), mode=APPEND)
        expected = [[x,] for x in 'A,B,C,c,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_down_last_perpend(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('f'), relative_to=find('F'))
        expected = [[x,] for x in 'A,B,C,D,E,f,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,d,e'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_down_last_append(self):
        parent = 'A,B,C,D,E,F'.split(',')[randint(0,5)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('f'), relative_to=find('F'), mode=APPEND)
        expected = [[x,] for x in 'A,B,C,D,E,F,f'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,d,e'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_first_prepend(self):
        parent = 'A,C,D,E,F'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('B'), relative_to=find('a'))
        expected = [[x,] for x in 'A,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'B,a,b,c,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_first_append(self):
        parent = 'A,C,D,E,F'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('B'), relative_to=find('a'), mode=APPEND)
        expected = [[x,] for x in 'A,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,B,b,c,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_middle_prepend(self):
        parent = 'B,C,D,E,F'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('A'), relative_to=find('d'))
        expected = [[x,] for x in 'B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,A,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_middle_append(self):
        parent = 'B,C,D,E,F'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('A'), relative_to=find('c'), mode=APPEND)
        expected = [[x,] for x in 'B,C,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,A,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_last_perpend(self):
        parent = 'A,B,C,D,E'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('F'), relative_to=find('f'))
        expected = [[x,] for x in 'A,B,C,D,E'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,d,e,F,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_one_up_last_append(self):
        parent = 'A,B,C,D,E'.split(',')[randint(0,4)]
        insert(self.subtree, parent=find(parent))
        Menu.relocate(find('F'), relative_to=find('f'), mode=APPEND)
        expected = [[x,] for x in 'A,B,C,D,E'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == parent:
                expected[i].append([[x,] for x in 'a,b,c,d,e,f,F'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_sub_tree_prepend(self):
        insert(self.subtree, parent=find('A'))
        Menu.relocate(find('A'), relative_to=find('D'))
        expected = [[x,] for x in 'B,C,A,D,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == 'A':
                expected[i].append([[x,] for x in 'a,b,c,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_move_sub_tree_prepend(self):
        insert(self.subtree, parent=find('A'))
        Menu.relocate(find('A'), relative_to=find('D'), mode=APPEND)
        expected = [[x,] for x in 'B,C,D,A,E,F'.split(',')]
        for i in range(len(expected)):
            if expected[i][0] == 'A':
                expected[i].append([[x,] for x in 'a,b,c,d,e,f'.split(',')])
                break
        self.assertEqualTree(expected)

    def test_append_to_node(self):
        Menu.relocate(find('F'), relative_to=find('E'), mode=SUBTREE)
        expected = [['A',],['B',],['C',],['D',],['E',['F',]],]
        self.assertEqualTree(expected)

        Menu.relocate(find('B'), relative_to=find('A'), mode=SUBTREE)
        expected = [['A',['B',]],['C',],['D',],['E',['F',]],]
        self.assertEqualTree(expected)

        Menu.relocate(find('D'), relative_to=find('C'), mode=SUBTREE)
        expected = [['A',['B',]],['C',['D',]],['E',['F',]],]
        self.assertEqualTree(expected)

        Menu.relocate(find('C'), relative_to=find('A'), mode=SUBTREE)
        expected = [['A',[['B',],['C',['D',]]]],['E',['F',]],]
        self.assertEqualTree(expected)

        Menu.relocate(find('A'), relative_to=find('F'), mode=SUBTREE)
        expected = (('E',(('F',(('A',(('B',),('C',('D',)),)),)),)),)
        self.assertEqualTree(expected)

        Menu.relocate(find('C'), relative_to=find('B'), mode=SUBTREE)
        expected = (('E',(('F',(('A',(('B',(('C',('D',)),)),)),)),)),)
        self.assertEqualTree(expected)

        Menu.relocate(find('B'), relative_to=find('E'), mode=APPEND)
        Menu.relocate(find('F'), relative_to=find('E'), mode=APPEND)
        Menu.relocate(find('C'), relative_to=find('E'), mode=APPEND)
        Menu.relocate(find('A'), relative_to=find('E'), mode=APPEND)
        Menu.relocate(find('D'), relative_to=find('E'))
        expected = ((x,) for x in 'D,E,A,C,F,B'.split(','))
        self.assertEqualTree(expected)

    def test_remove_simple(self):
        Menu.remove(find('A'))
        Menu.remove(find('F'), all=True)
        expected = ((x,) for x in 'B,C,D,E'.split(','))
        self.assertEqualTree(expected)

    def test_remove_complex_all(self):
        insert(self.subtree, parent=find('A'))
        Menu.remove(find('A'), all=True)
        expected = ((x,) for x in 'B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)

    def test_remove_complex_node_only(self):
        insert(self.subtree, parent=find('A'))
        Menu.remove(find('A'))
        expected = ((x,) for x in 'a,b,c,d,e,f,B,C,D,E,F'.split(','))
        self.assertEqualTree(expected)
