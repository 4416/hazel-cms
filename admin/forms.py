# -*- coding: utf-8 -*-

from wtforms import Form, BooleanField, HiddenField, TextField, PasswordField, validators
from wtforms import DateTimeField, TextAreaField, SelectField, SubmitField, FileField

class FolderForm(Form):
    name = TextField(u'Foldername', [validators.length(min=4, max=25)])
    slug = TextField(u'Slug')
    breadcrumb = TextField(u'Breadcrumb')
    state = SelectField(u'State', choices=[(0, 'Hidden'),
                                           (1, 'Draft'),
                                           (2, 'Published')],
                        coerce=int)
    active = BooleanField(u'Enabled')
    save = SubmitField(u'Save')
    cont = SubmitField(u'Save and Continue Editing')

class PageForm(FolderForm):
    name = TextField(u'Page Title', [validators.length(min=4, max=25)])
    description = TextAreaField(u'Description')
    keywords = TextField(u'Keywords')
    body = TextAreaField(u'Body')
    layout = SelectField(u'Layout')
    content_type = SelectField(u'Content-Type',
                               choices=[('text/html', 'HTML'),
                                        ('text/css', 'Stylesheet'),
                                        ('application/x-javascript', 'JavaScript'),
                                        ('text/plain', 'Plain text'),
                                        ('application/xhtml+xml', 'XHTML'),
                                        ('text/xml', 'XML')])

class BlockAddForm(Form):
    name = TextField(u'Blockname')
    add = SubmitField(u'Add Block')
    
class BlockForm(Form):
    body = TextAreaField(u'Body')

class ConfirmDeleteForm(Form):
    drop = SubmitField(u'Delete Page only')
    cascade = SubmitField(u'Delete Page and affected Pages')

class LayoutForm(Form):
    name = TextField(u'Layout Title', [validators.length(min=4, max=25)])
    body = TextAreaField(u'Body')

    active = BooleanField(u'Enabled')

    save = SubmitField(u'Save')
    cont = SubmitField(u'Save and Continue Editing')

class ConfirmDeleteLayoutForm(Form):
    drop = SubmitField(u'Delete Layout')
    
class FileForm(FolderForm):
    name = TextField(u'Filename', [validators.length(min=1, max=25)])
    file = FileField(u'File')

class FileEditForm(FolderForm):
    name = TextField(u'Filename', [validators.length(min=1, max=25)])

class FileConfirmDeleteForm(Form):
    drop = SubmitField(u'Delete File')
    cascade = SubmitField(u'Delete File and affected Files')

class ArticleForm(Form):
    title     = TextField(u'Title')
    city      = TextField(u'City')
    country   = TextField(u'Country')
    topics    = TextField(u'Topics')
    body      = TextAreaField(u'Body')
    published = BooleanField(u'Published')
    pub_date  = DateTimeField(u'Publish Date')

    save = SubmitField(u'Save')
    cont = SubmitField(u'Save and Continue Editing')
