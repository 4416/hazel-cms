# -*- coding: utf-8 -*-
from re import match
from werkzeug import redirect

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
    return render_template('admin/index.html', nuts=nuts)

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
    return render_template('configure.html', nuts=nuts, updated=updated)

from hazel.util.net import Response
from struct import pack
from logging import info
def pb(request, kind):
    resp = Response(mimetype="application/protocol-buffer-set", content_type="application/protocol-buffer-set")
    module, obj = kind.rsplit('.',1)
    info(module)
    info(obj)
    mod = __import__(module, fromlist=[module.rsplit('.',1)])
    info(mod)
    model = getattr(mod,obj)
    for e in model.all():
        pb = e._entity._ToPb()
        resp.stream.write(pack('I',pb.ByteSize()))
        resp.stream.write(pb.Encode())
    return resp
