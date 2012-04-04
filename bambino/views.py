from pyramid.view import view_config
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from appenv import AppEnv

import json
import logging
import requests

log = logging.getLogger(__name__)

@view_config(route_name='applications', renderer='json')
def my_view(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    appenv = AppEnv(web_apps_dir)
    
    return appenv.repo_data


@subscriber(ApplicationCreated)
def register_me(event):
    """
    Register this Bambino node with Doula.
    """
    settings = event.app.registry.settings
    
    node = {
        'name': settings['node'],
        'site': settings['site'],
        'url' : settings['bambino_url']
    }
    
    payload = {'node': json.dumps(node)}
    
    try:
        requests.post(settings['register_url'], data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)
