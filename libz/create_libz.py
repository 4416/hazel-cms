# -*- coding: utf-8 -*-
# too bad this does not work on GAE
import sys
import zipfile

libs = (
    ('werkzeug.zip', '../../lib/werkzeug-main/werkzeug'),
    ('jinja2.zip',   '../../lib/jinja2-main/jinja2'),
    ('wtforms.zip',  '../../lib/wtforms/wtforms')
)

if __name__ == '__main__':
    for fn, path in libs:
        zf = zipfile.PyZipFile(fn, mode='w')
        try:
            zf.debug = 3
            print 'Adding python files'
            zf.writepy(path)
        finally:
            zf.close()
        for name in zf.namelist():
            print name
