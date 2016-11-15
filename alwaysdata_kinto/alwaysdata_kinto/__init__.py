"""Main entry point
"""
from pyramid.static import static_view
from pyramid.config import Configurator

from .constants import REDIS_HOST, REDIS_PORT, REDIS_DB


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("alwaysdata_kinto.views")

    config.registry.hmac_secret = settings['hmac_secret']

    config.registry.redis = {
        'host': settings.get('redis.host', REDIS_HOST),
        'port': int(settings.get('redis.port', REDIS_PORT)),
        'db': int(settings.get('redis.db', REDIS_DB))
    }

    # Serve the web interface
    build_dir = static_view('alwaysdata_kinto:build', use_subpath=True)
    config.add_route('catchall_static', '/*subpath')
    config.add_view(build_dir, route_name="catchall_static")

    return config.make_wsgi_app()
