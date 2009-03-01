# -*- coding: utf-8 -*-
from wtforms import Form
from wtforms import SubmitField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import BooleanField
from wtforms import validators

class SaveContinueForm(Form):
    save = SubmitField(u'Save')
    cont = SubmitField(u'Save and Continue Editing')

class DeleteForm(Form):
    drop = SubmitField(u'Delete')

class FolderForm(SaveContinueForm):
    name = TextField(u'Foldername', [validators.length(min=2, max=25)])
    slug = TextField(u'Slug')

class LayoutForm(SaveContinueForm):
    name = TextField(u'Layout Title', [validators.length(min=2, max=25)])
    body = TextAreaField(u'Body')
