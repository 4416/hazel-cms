# -*- coding: utf-8 -*-
file_ext_to_content_type = { 'jpg': 'image/jpeg',
                             'gif': 'image/gif',
                             'css': 'text/css',
                             'txt': 'text/plain',
                             'png': 'image/png',
                             'xml': 'text/xml',
                             'js' : 'application/x-javascript',
                             'pdf': 'application/pdf',
                             'html': 'text/html' }
content_type_to_file_ext = dict([(v,k) for k,v in file_ext_to_content_type.items()])
