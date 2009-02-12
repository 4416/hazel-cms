# -*- coding: utf-8 -*-
from zipfile import ZipFile
from os.path import dirname
from os.path import abspath
from os.path import join
from util.net import Response
from util.decorators import memcached
from util.constants import file_ext_to_content_type

zf = ZipFile(join(abspath(dirname('__file__')), 'zip', 'famfamfam.zip'))

@memcached
def get(request, file):
    data = zf.read(file)
    return Response(data, mimetype=file_ext_to_content_type[file.rsplit('.',1)[1]])
