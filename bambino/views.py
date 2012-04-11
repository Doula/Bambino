from pyramid.view import view_config
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from appenv import Node

import poll
import json
import logging
import requests
import time

log = logging.getLogger(__name__)

@view_config(route_name='applications', renderer='json')
def applications(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    node = Node(web_apps_dir)
    
    return node.repo_data

@view_config(route_name='tag', renderer='json')
def tag(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    node = Node(web_apps_dir)
    apps = [s.strip() for s in request.POST['apps'].split(',')]
    return node.tag_apps(apps,
                  request.POST['tag'],
                  request.POST['description'])

@subscriber(ApplicationCreated)
def register_me(event):
    """
    Register this Bambino node with Doula.
    """
    poll.start_heartbeat()
    
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
