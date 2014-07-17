from pyramid.view import view_config


@view_config(route_name='home', renderer='templates/home.mak')
def my_view(request):
    return {'project': 'essos'}
