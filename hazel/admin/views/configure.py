# -*- coding: utf-8 -*-
from re import match
from werkzeug import redirect

from hazel.models.restoremap import RestoreMap

from hazel.util.helper import render_template
from hazel.util.globals import url_for

def list(request):
    from hazel import NutSettings as AppSettings
    nuts = []
    _nut = {'name': '__name__',
            'title': '__title__',
            'version': '__version__',
            'admin': '__admin__',
            'doc': '__doc__'}
    for nut in AppSettings().nuts:
        module = __import__('hazel.nuts.%s' % nut, fromlist=['hazel.nuts'])
        nuts.append(dict(map(lambda (key, prop): (key, getattr(module, prop, None)),
                             _nut.items())))
    return render_template('app/admin/index.html', nuts=nuts)

def nut(request):
    from hazel import NutSettings, SettingsForm, handle_form_data
    nuts = {'hazel' : {'settings' : NutSettings,
                       'form': SettingsForm(request.form, obj=NutSettings(), \
                                            prefix='hazel_config') }}
    handler = {'hazel' : handle_form_data }
    for nut in NutSettings().nuts:
        # load the Settings, Form and data handler from the
        # nuts.
        module = __import__('hazel.nuts.%s' % nut, fromlist=['hazel.nuts'])
        ns, sf, hd = map(lambda prop: getattr(module, prop, None),
                         ['NutSettings', 'SettingsForm', 'handle_form_data'])
        # if the nut does not provide a formmodule or no data handler
        # skip it. We won't be able to configure it anyway.
        if not sf or not hd:
            continue
        nuts[nut] = {'settings' : ns(),
                       'form': sf(request.form, obj=ns(), \
                                  prefix='%s_config' % nut)}
        handler[nut] = hd
    updated = False
    if request.method == 'POST' and all([nut['form'].validate()\
                                         for nut in nuts.values()]):
        # let all nuts handle their form.
        for nut in nuts:
            handler[nut](nuts[nut]['form'])
        updated = True
        return redirect(url_for('admin/configuration', message='updated'), 302)
    return render_template('app/configure.html', nuts=nuts, updated=updated)

from hazel.util.net import Response
from struct import pack
from struct import unpack
from struct import error
from logging import info
from google.appengine.api.datastore import Entity
from pickle import dumps
from pickle import loads
from google.appengine.ext import db
from google.appengine.api import users
from zlib import compress
from zlib import decompress

def pb(request, kind):
    resp = Response(mimetype="application/protocol-buffer-set", content_type="application/protocol-buffer-set")
    module, obj = kind.rsplit('.',1)
    mod = __import__(module, fromlist=[module.rsplit('.',1)])
    model = getattr(mod,obj)
    for e in model.all():
        pb = e._entity._ToPb()
        resp.stream.write(pack('I',pb.ByteSize()))
        resp.stream.write(pb.Encode())
    return resp

def pb_rec(request):
    if request.method != 'POST':
        return Response('POST required')
    f = request.files.get('file')
    while True:
        try:
            (l,) = unpack('I', f.read(4))
            info(l)
            e = Entity._FromPb(f.read(l))
            info(e)
        except Exception, e:
            info(e)
            break
    return Response('Posted!')

def encode(x):
    if isinstance(x, db.Model):
        return str(x.key())
    if isinstance(x, users.User):
        return x.email()
    return x


def eb(request, kind):
    resp = Response(mimetype="application/python-eval-dump", content_type="application/python-eval-dump")
    module, obj = kind.rsplit('.',1)
    mod = __import__(module, fromlist=[module.rsplit('.',1)])
    model = getattr(mod,obj)
    for p in model.all():
        data = (p.__module__, p.__class__.__name__, str(p.key()), [(x, encode(getattr(p,x))) for x in p.properties() if encode(x) is not None])
        pdata = compress(dumps(data,-1),9)
        resp.stream.write(pack('I',len(pdata)))
        resp.stream.write(pdata)
    return resp    

def eb_rec(request):
    if request.method != 'POST':
        return Response('POST required')
    f = request.files.get('file')
    key_map = {}
    def decode(x,y):
        if y is None:
            return y
        if isinstance(x, db.UserProperty):
            return users.User(email=y)
        if isinstance(x, db.ReferenceProperty):
            key = RestoreMap.sink_for_key(y)
            if key:
                return db.Key(key)
            return db.Key(y)
        return y
    while True:
        try:
            (l,) = unpack('I', f.read(4))
            t = loads(decompress(f.read(l)))
            mod = __import__(t[0], fromlist=[t[0]])
            kind = getattr(mod,t[1])
            key = db.Key(t[2])
            kwds = dict([(k,decode(getattr(kind, k), v)) for k,v in t[3]])
            if key.name():
                kwds['key_name'] = key.name()
            obj = kind(**kwds)
            obj.put()
            RestoreMap.create_or_update(str(key), sink=str(obj.key()))
        except error, e:
            break

    return Response('Posted!')

def fix_nodes(request):
    from hazel.nuts.pages.models import Node
    from hazel.models.restoremap import RestoreMap
    from google.appengine.ext import db

    _map = {}

    for m in RestoreMap.all():
        source = str(m.key().name())[7:]
        sink = m.sink
        if source != sink:
            _map[source] = m.sink

    def tryfix(x):
        if x in _map:
            return _map[x]
        return x

    for n in Node.all():
        for prop in ('siblings','children', 'ancestors'):
            setattr(n,prop,map(tryfix, getattr(n,prop)))
        n.put()
    db.delete(RestoreMap.all())

    return Response("Fixed!")
