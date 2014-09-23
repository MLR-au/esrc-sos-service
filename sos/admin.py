from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)

from common import *

@view_config(route_name='admin_users', request_method='GET', renderer='json')
def admin_users_get(request):
    # verify the token and session
    verify_session(request)

    print request.GET

@view_config(route_name='admin_users', request_method='POST', renderer='json')
def admin_users_post(request):
    # verify the token and session
    verify_session(request)

    print request.json_body