# -*- coding: utf-8 -*-
from zipfile import ZipFile
from utils import Response, file_ext_to_content_type, memcached
from os.path import dirname, abspath, join

zf = ZipFile(join(abspath(dirname('__file__')), 'zip', 'famfamfam.zip'))

@memcached
def get(request, file):
    data = zf.read(file)
    return Response(data, mimetype=file_ext_to_content_type[file.rsplit('.',1)[1]])
