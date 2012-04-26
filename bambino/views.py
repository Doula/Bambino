from pyramid.view import view_config
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from appenv import Node

import registration
import logging
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

@view_config(route_name='mark_as_deployed', renderer='json')
def mark_as_deployed(request):
    web_apps_dir = request.registry.settings['web_apps_dir']
    node = Node(web_apps_dir)
    apps = [s.strip() for s in request.POST['apps'].split(',')]
    
    return node.mark_as_deployed(apps, request.POST['tag'])


@subscriber(ApplicationCreated)
def register_me(event):
    """
    Register this Bambino node with Doula.
    """
    settings = event.app.registry.settings

    machine_info = Node.get_machine_info()
    #TODO: we're using the IP for now.  Once the hostname gets standardized, we'll
    # move to that
    machine_info['url'] = 'http://%s:%s' % (machine_info['ip'], settings['port'])

    registration.register_bambino(machine_info, settings['register_url'])


