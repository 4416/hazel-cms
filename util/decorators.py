from google.appengine.api import users
from utils import render_template

################################################################################
# decorator
################################################################################
def require_admin(fn):
    def _fn(request, *args, **kwargs):
        if not users.is_current_user_admin():
            return render_template('no_access.html',request=request)
        return fn(request, *args, **kwargs)
    return _fn
