NAME = hazel-cms
ROOT = `pwd`
PDFS = $(NAME).pdf

graph:
	grep "render_template(['\"]" hazel -R | grep -v '^lib/' | grep '.py:' | sed "s_\"_'_g" | sed "s_^\([^:]*\):[^']*'\([^']*\).*_(('$(ROOT)','\1'), ('$(ROOT)/templates','\2'))_g" > code-jinja.dep
	grep '{% extend' hazel/templates/ -R | sed "s_\"_'_g" | sed "s_^hazel/templates/\([^:]*\)[^']*'\([^']*\).*_(('$(ROOT)/templates', '\1'), ('$(ROOT)/templates', '\2'))_g" > templates.dep
	PYTHONPATH=/usr/local/google_appengine:./lib:$$PYTHONPATH sfood --follow --internal > code.dep
	cat *.dep | sfood-graph | dot -Tps | pstopdf -i -o hazel-all.pdf

flat:
	cat *.dep | sfood-flatten

check:
	@echo "sfood-checker"
	@echo "============="
	sfood-checker
	@echo "pyflakes"
	@echo "========"
	find . -name '*.py' | xargs pyflakes

lint:
	pylint *