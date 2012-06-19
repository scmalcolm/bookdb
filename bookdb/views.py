import re
from docutils.core import publish_parts

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

from pyramid.security import (
    remember,
    forget,
    authenticated_userid
    )

from .models import (
    DBSession,
    Book,
    ShelfLocation,
    Binding,
    Publisher,
    )

from .security import USERS


@view_config(route_name='front_page', renderer=';templates/front_page.pt')
def front_page(request):
    pass


@view_config(route_name='view_book', renderer='templates/single_book.pt')
def view_book(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).first()
    if book is None:
        return HTTPNotFound('No such book')
    edit_url = request.route_url('edit_book', isbn13=isbn13)
    return dict(book=book,
                edit_url=edit_url,
                logged_in=authenticated_userid(request),
                editable=False,
                )


@view_config(route_name='edit_book', renderer='templates/single_book.pt', permission='edit')
def edit_book(request):
    isbn13 = request.matchdict['isbn13']
    book = DBSession.query(Book).filter_by(isbn13=isbn13).one()
    if 'form.submitted' in request.params:
        # TODO: get updated data from request and update the book object
        DBSession.add(book)
        return HTTPFound(location=request.route_url(view_book, isbn13=isbn13))
    bindings = DBSession.query(Binding).all()
    locations = DBSession.query(ShelfLocation).all()
    publishers = DBSession.query(Publisher).all()
    return dict(book=book,
                save_url=request.route_url('edit_book', isbn13=isbn13),
                logged_in=authenticated_userid(request),
                editable=True,
                bindings=bindings,
                locations=locations,
                publishers=publishers,
                )


@view_config(route_name='login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        if USERS.get(login) == password:
            headers = remember(request, login)
            return HTTPFound(location=came_from, headers=headers)
        message = 'Failed login'

    return dict(message=message,
                url=request.application_url + '/login',
                came_from=came_from,
                login=login,
                password=password,
                )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('front_page'), headers=headers)
