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
        exec 'from hazel.nuts.%s import NutSettings, SettingsForm, handle_form_data' % nut
        nuts[nut] = {'settings' : NutSettings(),
                       'form': SettingsForm(request.form, obj=NutSettings(), \
                                            prefix='%s_config' % nut)}
        handler[nut] = handle_form_data
    updated = False
    if request.method == 'POST' and all([nut['form'].validate()\
                                         for nut in nuts.values()]):
        for nut in nuts:
            handler[nut](nuts[nut]['form'])
        updated = True
        return redirect(url_for('admin/configuration', message='updated'), 302)
    return render_template('configure.html', nuts=nuts, updated=updated)
