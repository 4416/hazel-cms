# -*- coding: utf-8 -*-
from re import match
from werkzeug import redirect

from hazel.util.helper import render_template
from hazel.util.globals import url_for

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
