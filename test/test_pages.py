# -*- coding: utf-8 -*-
################################################################################
# Test for the pages
################################################################################
# Author: Moritz Angermann
# Date: 07-02-2009

from google.appengine.ext import db

from models.pages import Node as TestPage
from models.pages import HIDDEN, DRAFT, PUBLISHED
from models.pages import FOLDER, PAGE, FILE
import unittest

class PagesTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add(self):
        page = TestPage.add(type=PAGE,
                            name=u'Test Name',
                            body=u'',
                            author=None,
                            state=PUBLISHED,
                            active=True,
                            description=u'blah',
                            keywords = u'foo, bar',
                            slug=u'test-name',
                            layout=None)
        self.assertEqual(page.abs_path, 'test-name')

    def test_add_with_folder(self):
        folder = TestPage.add(type=FOLDER,
                              name=u'Foo',
                              slug=u'foo',
                              author=None,
                              active=True,
                              state=PUBLISHED,
                              description=u'blah',
                              keywords='')
        page = TestPage.add(to=folder.get_key(),
                            type=PAGE,
                            name=u'Test Name',
                            body=u'',
                            author=None,
                            state=PUBLISHED,
                            active=True,
                            description=u'blah',
                            keywords = u'foo, bar',
                            slug=u'test-name',
                            layout=None)
        self.assertEqual(folder.abs_path, 'foo')
        self.assertEqual(page.abs_path, 'foo/test-name')

    def test_put(self):
        folder = TestPage.add(type=FOLDER,
                              name=u'Foo',
                              slug=u'foo',
                              author=None,
                              active=True,
                              state=PUBLISHED,
                              description=u'blah',
                              keywords='')
        page = TestPage.add(to=folder.get_key(),
                            type=PAGE,
                            name=u'Test Name',
                            body=u'',
                            author=None,
                            state=PUBLISHED,
                            active=True,
                            description=u'blah',
                            keywords = u'foo, bar',
                            slug=u'test-name',
                            layout=None)
        # check integrity
        self.assertEqual(folder.abs_path, u'foo')
        self.assertEqual(page.abs_path, u'foo/test-name')

        # change leaf
        page.slug = u'name-test'
        page.update()
        folder, page = db.get([folder.key(), page.key()])
        self.assertEqual(folder.abs_path, u'foo')
        self.assertEqual(page.abs_path, u'foo/name-test')

        # change node
        folder.slug = u'bar'
        folder.update()
        folder, page = db.get([folder.key(), page.key()])
        self.assertEqual(folder.abs_path, u'bar')
        self.assertEqual(page.abs_path, u'bar/name-test')

    def test_remove(self):
        folder = TestPage.add(type=FOLDER,
                              name=u'Foo',
                              slug=u'foo',
                              author=None,
                              active=True,
                              state=PUBLISHED,
                              description=u'blah',
                              keywords='')
        page = TestPage.add(to=folder.get_key(),
                            type=PAGE,
                            name=u'Test Name',
                            body=u'',
                            author=None,
                            state=PUBLISHED,
                            active=True,
                            description=u'blah',
                            keywords = u'foo, bar',
                            slug=u'test-name',
                            layout=None)

        # check integrity
        self.assertEqual(folder.abs_path, u'foo')
        self.assertEqual(page.abs_path, u'foo/test-name')

        # drop folder
        TestPage.drop(folder.get_key())
        folder, page = db.get([folder.key(), page.key()])
        self.assertEqual(page.abs_path, u'test-name')
