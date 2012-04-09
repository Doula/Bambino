from pyramid.config import Configurator

def main(global_config, **settings):
    """ 
    Serve the Bambino application.
    """
    config = Configurator(settings=settings)
    config.add_route('applications', '/applications')
    config.add_route('tag', '/tag')
    config.scan()
    
    return config.make_wsgi_app()
