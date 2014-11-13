from pyramid.config import Configurator


def main(global_config, **settings):
    """
    Serve the Bambino application.
    """
    config = Configurator(settings=settings)
    config.add_route('services', '/services')
    config.add_route('tag', '/tag')
    config.add_route('mark_as_deployed', 'deploy/mark')
    config.scan()

    return config.make_wsgi_app()
