from pyramid.config import Configurator
from pyramid.paster import setup_logging

from config import Config as appConfig

from connectors import CassandraBackend

def init_cassandra_connection(conf):
    arguments = {
        'nodes': conf['nodes'],
        'user': conf['user'],
        'pass': conf['pass'],
        'keyspace': conf['keyspace']
    }
    c = CassandraBackend(arguments)
    return c.session
 

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    setup_logging(global_config['__file__'])

    # initialise a connection to cassandra on startup and store the region
    #  in the registry which will be injected into each request
    conf = appConfig(config.registry.settings.get('app.config'))
    config.registry.app_config = conf.app_config
    config.registry.app_config['cassandra']['session'] = init_cassandra_connection(config.registry.app_config['cassandra'])

    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('admin', '/admin')
    config.add_route('logout', '/logout')
    config.add_route('health_check', '/health-check')
    config.add_route('login_staff', '/login/staff')
    config.add_route('login_google', '/login/google')
    config.add_route('login_linkedin', '/login/linkedin')
    config.scan()
    return config.make_wsgi_app()
