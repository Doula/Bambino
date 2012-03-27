from pyramid.view import view_config
from appenv import AppEnv
import json

@view_config(route_name='applications', renderer='json')
def my_view(request):
    # /Users/alexvazquezOLD/boxes/code_dot_corp/webappdir
    web_app_dir = '/Users/alexvazquezOLD/boxes/code_dot_corp/webappdir'
    appenv = AppEnv(web_app_dir)
    payload = dict(status='ok', payload=appenv.repo_data)
    
    return json.dumps(payload)
