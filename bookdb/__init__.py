from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from bookdb.security import groupfinder

from .models import DBSession


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    authn_policy = AuthTktAuthenticationPolicy('sosecret', callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
                          root_factory='bookdb.models.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('front_page', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('book_list',   '/book/list')
    config.add_route('book_add',    '/book/add')
    config.add_route('book_view',   '/book/{isbn13}')
    config.add_route('book_edit',   '/book/{isbn13}/edit')
    config.add_route('book_delete', '/book/{isbn13}/delete')

    config.add_route('order_list',   '/order/list')
    config.add_route('order_add',    '/order/add')
    config.add_route('order_view',   '/order/{po}')
    config.add_route('order_edit',   '/order/{po}/edit')
    config.add_route('order_delete', '/order/{po}/delete')
    config.add_route('order_pdf',    '/order/{po}/pdf')
    config.add_route('order_entry_delete', '/order/{po}/delete_entry/{isbn13}')

    config.add_route('distributor_list',   '/distributor/list')
    config.add_route('distributor_add',    '/distributor/add')
    config.add_route('distributor_view',   '/distributor/{short_name}')
    config.add_route('distributor_edit',   '/distributor/{short_name}/edit')
    config.add_route('distributor_delete', '/distributor/{short_name}/delete')

    config.add_route('publisher_list',   '/publisher/list')
    config.add_route('publisher_add',    '/publisher/add')
    config.add_route('publisher_edit',   '/publisher/{short_name}/edit')

    config.scan()
    return config.make_wsgi_app()
