
from pyramid.view import view_defaults
from pyramid.view import view_config

from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPNotFound
)

@view_config(route_name="get_users", request_method="OPTIONS")
def get_users_options(request):
    print 'get user options', request.referrer
    request.response.headers['Access-Control-Allow-Origin'] = request.referrer.rstrip('/')
    request.response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, POST'
    request.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With, content-type'
    raise HTTPOk(headers=request.response.headers)

@view_config(route_name="get_users", request_method="POST", renderer='json')
def get_users(self, request):
    # only set the allow origin header if the referrer is one of our apps
    if validate_app_redirect(request, request.referrer):
        request.response.headers['Access-Control-Allow-Origin'] = request.referrer.rstrip('/')
        request.response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, POST'
        request.response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With, content-type'
    else:
        return {}

    print request.POST

