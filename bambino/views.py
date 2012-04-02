from pyramid.view import view_config
from appenv import Node
import json

@view_config(route_name='applications', renderer='json')
def applications(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    print web_apps_dir
    appenv = Node(web_apps_dir)
    payload = dict(status='ok', payload=appenv.repo_data)
    print payload
    return json.dumps(payload)


@view_config(route_name='tag', renderer='json')
def tag(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    appenv = Node(web_apps_dir)
