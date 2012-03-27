from pyramid.view import view_config
from appenv import AppEnv
import json

@view_config(route_name='applications', renderer='json')
def my_view(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    appenv = AppEnv(web_apps_dir)
    payload = dict(status='ok', payload=appenv.repo_data)
    
    print json.dumps(payload)
    
    return json.dumps(payload)
