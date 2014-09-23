from pyramid.config import Configurator
from pyramid.paster import setup_logging
from pyramid.renderers import JSONP

from config import Config as appConfig

from connectors import MongoBackend
import auth_providers

from pyramid.session import SignedCookieSessionFactory

def init_mongodb_connection(conf):
    m = MongoBackend()
    m.connect(conf)
    return m.client
 

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    setup_logging(global_config['__file__'])

    # initialise a connection to mongo on startup and store the client 
    #  in the registry which will be injected into each request
    conf = appConfig(config.registry.settings.get('app.config'))
    config.registry.app_config = conf.app_config
    config.registry.app_config['mongodb']['client'] = init_mongodb_connection(config.registry.app_config['mongodb'])

    # a session factory is required by velruse but we'll grab the password from the
    #  datafile that has all the other secret stuff we don't want in git
    session_factory = SignedCookieSessionFactory(auth_providers.session_secret)
    config.set_session_factory(session_factory)

    # pull in the login provider information
    auth_providers.add_providers(config)

    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.add_route('home', '/')
    config.add_route('health_check', '/health-check')

    # login routes
    config.add_route('login_staff', '/login/staff')
    config.add_route('login_google', '/login/google')
    config.add_route('login_linkedin', '/login/linkedin')

    # retrieve / validate tokens
    config.add_route('retrieve_token', '/token/{code}')
    config.add_route('validate_token', '/token')

    # admin components
    config.add_route('admin_users', '/admin/users/{user}')

    config.scan()
    return config.make_wsgi_app()
