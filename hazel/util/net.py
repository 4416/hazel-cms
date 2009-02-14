# -*- coding: utf-8 -*-
# Request
from werkzeug import BaseRequest
from werkzeug import AcceptMixin
from werkzeug import ETagRequestMixin
# Response
from werkzeug import BaseResponse
from werkzeug import ETagResponseMixin
from werkzeug import ResponseStreamMixin
from werkzeug import CommonResponseDescriptorsMixin

################################################################################
# network classes
################################################################################
class Request(BaseRequest, AcceptMixin, ETagRequestMixin):
    pass

class Response(BaseResponse, ETagResponseMixin, ResponseStreamMixin,\
               CommonResponseDescriptorsMixin):
    pass
