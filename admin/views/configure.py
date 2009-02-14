# -*- coding: utf-8 -*-
from re import match
from werkzeug import redirect

from util.helper import render_template

def nut(request, nut):
    if not match(r'^[a-z]+$', nut):
        return redirect('/')
    exec 'from nuts.%s import NutSettings, SettingsForm, handle_form_data' % nut
    form = SettingsForm(request.form, obj=NutSettings(), prefix='%s_config' % nut)
    updated = False
    if request.method == 'POST' and form.validate():
        handle_form_data(form)
        updated = True
    return render_template('configure.html', nut=nut, form=form,
                           updated=updated, settings=NutSettings())
