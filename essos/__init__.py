from pyramid.config import Configurator
from pyramid.paster import setup_logging


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    setup_logging(global_config['__file__'])
    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('health_check', '/health-check')
    config.add_route('login_staff', '/login/staff')
    config.add_route('login_google', '/login/google')
    config.add_route('login_linkedin', '/login/linkedin')
    config.scan()
    return config.make_wsgi_app()
