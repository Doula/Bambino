from pyramid.view import view_config

@view_config(route_name='applications', renderer='json')
def my_view(request):
    # make a call to tim's code right here
    return {'project':'Bambino'}
