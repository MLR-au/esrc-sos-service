from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError
)

from config import Config
import auth

from cassandra.cluster import Cluster
import logging
log = logging.getLogger()

@view_config(route_name="health_check", renderer="string")
def health_check(request):
    conf = Config(request)

    # can we connect to an LDAP server
    lc = conf.app_config['ldap']
    conn = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    if conn.conn is None:
        raise HTTPInternalServerError

    return 'OK'


@view_config(route_name='home', renderer='templates/home.mak')
def my_view(request):
    r = ''
    if request.GET.has_key('r'):
        r = request.GET['r']

    e = False
    if request.GET.has_key('e'):
        e = request.GET['e']

    log.info("Login redirect from: '%s', remote address: %s" % (r, request.environ['REMOTE_ADDR']))
    return { 'r': r, 'e': e }

@view_config(route_name='login_staff', renderer='json')
def login_staff(request):
    conf = Config(request)

    lc = conf.app_config['ldap']
    conn = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = conn.authenticate(request.POST['username'], request.POST['password'])
    try:
        r = request.POST['r']
    except KeyError:
        r = None

    if not result and r:
        raise HTTPFound("/?r=%s&e=True")
    elif not result:
        raise HTTPFound('/?e=True')
    elif result and r:
        raise HTTPFound(r)
    else:
        raise HTTPFound('/profile')

    return {}
