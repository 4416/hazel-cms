# -*- coding: utf-8 -*-

class StringListWidget(TextInput):
    def render(self, name, value, *args, **kwargs):
        if not value is None:
            value = ', '.join(value.split('\n'))
        return super(StringListWidget,self).render(name,value,*args, **kwargs)
    def value_from_datadict(self, data, files, name):
        data = data.get(name, None)
        if data is None:
            return None
        data = '\n'.join([tag.strip() for tag in data.split(',')])
        return data
